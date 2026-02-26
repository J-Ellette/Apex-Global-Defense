use std::collections::HashMap;
use std::pin::Pin;
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};

use rand::rngs::SmallRng;
use rand::{Rng, SeedableRng};
use tokio::sync::RwLock;
use tokio::time::{sleep, Duration};
use tokio_stream::{wrappers::ReceiverStream, Stream};
use tonic::{transport::Server, Request, Response, Status};
use tracing::info;
use uuid::Uuid;

pub mod sim {
    tonic::include_proto!("agd.sim");
}

use sim::sim_engine_server::{SimEngine, SimEngineServer};
use sim::{
    Ack, EventInjection, EventType, ForceStatus, GeoPoint, RunRef, RunStatus, ScenarioConfig,
    SimEvent, SimRequest, SimState,
};

// ── Weather modifiers ────────────────────────────────────────────────────────
// Multiplier applied to attacker combat effectiveness.
const WEATHER_MODS: &[(&str, f64)] = &[
    ("clear", 1.00),
    ("overcast", 0.95),
    ("rain", 0.85),
    ("fog", 0.70),
    ("storm", 0.55),
    ("snow", 0.60),
];

// ── Terrain modifiers ────────────────────────────────────────────────────────
// Multiplier applied to defender combat effectiveness (terrain favours defenders).
const TERRAIN_MODS: &[(&str, f64)] = &[
    ("flat", 1.00),
    ("urban", 1.30),
    ("mountainous", 1.45),
    ("jungle", 1.35),
    ("desert", 0.90),
];

fn weather_mod(preset: &str) -> f64 {
    WEATHER_MODS
        .iter()
        .find(|(k, _)| *k == preset)
        .map(|(_, v)| *v)
        .unwrap_or(1.0)
}

fn terrain_mod(preset: &str) -> f64 {
    TERRAIN_MODS
        .iter()
        .find(|(k, _)| *k == preset)
        .map(|(_, v)| *v)
        .unwrap_or(1.0)
}

// ── Unit and Force state ─────────────────────────────────────────────────────

/// Per-unit runtime state tracked inside the engine.
#[derive(Clone, Debug)]
struct UnitState {
    lat: f64,
    lng: f64,
    /// Fractional strength remaining [0, 1].
    strength: f64,
    /// Supply levels [0, 1].
    ammo: f64,
    fuel: f64,
}

impl UnitState {
    fn new(rng: &mut SmallRng) -> Self {
        Self {
            lat: rng.gen_range(-10.0..10.0),
            lng: rng.gen_range(30.0..60.0),
            strength: 1.0,
            ammo: 1.0,
            fuel: 1.0,
        }
    }
}

/// Aggregated force-level stats derived from all units on one side.
#[derive(Clone, Debug, Default)]
struct ForceState {
    units: Vec<UnitState>,
    total_kia: i32,
    total_wia: i32,
    objectives_held: i32,
    armor_losses: i32,
    arty_losses: i32,
    air_losses: i32,
}

impl ForceState {
    fn unit_count(&self) -> i32 {
        self.units.len() as i32
    }

    fn strength_pct(&self) -> f64 {
        if self.units.is_empty() {
            return 0.0;
        }
        let sum: f64 = self.units.iter().map(|u| u.strength).sum();
        sum / self.units.len() as f64
    }

    fn avg_ammo(&self) -> f64 {
        if self.units.is_empty() {
            return 0.0;
        }
        self.units.iter().map(|u| u.ammo).sum::<f64>() / self.units.len() as f64
    }

    fn avg_fuel(&self) -> f64 {
        if self.units.is_empty() {
            return 0.0;
        }
        self.units.iter().map(|u| u.fuel).sum::<f64>() / self.units.len() as f64
    }

    fn to_proto(&self) -> ForceStatus {
        let eq_json = serde_json::json!({
            "armor": self.armor_losses,
            "artillery": self.arty_losses,
            "aircraft": self.air_losses,
        })
        .to_string();
        ForceStatus {
            unit_count: self.unit_count(),
            strength_pct: self.strength_pct(),
            total_kia: self.total_kia,
            total_wia: self.total_wia,
            supply_ammo: self.avg_ammo(),
            supply_fuel: self.avg_fuel(),
            // Rations modeled at force level (not yet per-unit); default to full.
            supply_rations: 1.0,
            equipment_losses_json: eq_json,
            objectives_held: self.objectives_held,
        }
    }
}

// ── Objective state ──────────────────────────────────────────────────────────

#[derive(Clone, Debug)]
enum ObjControl {
    Neutral,
    Blue,
    Red,
}

#[derive(Clone, Debug)]
struct ObjectiveState {
    id: String,
    lat: f64,
    lng: f64,
    control: ObjControl,
}

// ── Per-run runtime state ────────────────────────────────────────────────────

#[derive(Clone, Debug)]
struct RunRuntimeState {
    status: String,
    progress: f64,
    turn_number: i32,
    total_turns: i32,
    config: ScenarioConfig,
    blue: ForceState,
    red: ForceState,
    objectives: Vec<ObjectiveState>,
    /// Turn snapshots keyed by turn number (stored as serialised SimState JSON).
    snapshots: HashMap<i32, SimState>,
}

impl RunRuntimeState {
    fn build_sim_state(&self, run_id: &str) -> SimState {
        let obj_map: serde_json::Map<String, serde_json::Value> = self
            .objectives
            .iter()
            .map(|o| {
                let label = match &o.control {
                    ObjControl::Blue => "BLUE",
                    ObjControl::Red => "RED",
                    ObjControl::Neutral => "CONTESTED",
                };
                (o.id.clone(), serde_json::Value::String(label.to_string()))
            })
            .collect();

        let snapshot_bytes = serde_json::to_vec(&serde_json::json!({
            "turn": self.turn_number,
            "blue_strength": self.blue.strength_pct(),
            "red_strength": self.red.strength_pct(),
            "blue_kia": self.blue.total_kia,
            "red_kia": self.red.total_kia,
        }))
        .unwrap_or_default();

        SimState {
            run_id: run_id.to_string(),
            status: self.status.clone(),
            progress: self.progress,
            turn_number: self.turn_number,
            sim_time_ms: SimEngineService::now_ms(),
            blue_unit_count: self.blue.unit_count(),
            red_unit_count: self.red.unit_count(),
            objectives_status_json: serde_json::Value::Object(obj_map).to_string(),
            blue_force: Some(self.blue.to_proto()),
            red_force: Some(self.red.to_proto()),
            snapshot: snapshot_bytes,
        }
    }
}

#[derive(Clone, Default)]
struct EngineState {
    runs: Arc<RwLock<HashMap<String, RunRuntimeState>>>,
}

#[derive(Clone, Default)]
struct SimEngineService {
    state: EngineState,
}

impl SimEngineService {
    fn now_ms() -> i64 {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis() as i64
    }

    fn turns_from_config(cfg: &ScenarioConfig) -> i32 {
        let hours = if cfg.duration_hours <= 0 { 24 } else { cfg.duration_hours };
        std::cmp::max(1, hours / 4)
    }

    /// Derive a deterministic seed from the run_id string hash.
    fn seed_from_run_id(run_id: &str) -> u64 {
        use std::hash::{Hash, Hasher};
        let mut hasher = std::collections::hash_map::DefaultHasher::new();
        run_id.hash(&mut hasher);
        hasher.finish()
    }

    /// Initialise force units from a list of force IDs.
    fn init_force(ids: &[String], rng: &mut SmallRng) -> ForceState {
        let n = if ids.is_empty() { 10 } else { ids.len() };
        let units = (0..n).map(|_| UnitState::new(rng)).collect();
        ForceState {
            units,
            ..Default::default()
        }
    }

    /// Initialise 6 neutral objectives spread across the theater.
    fn init_objectives(rng: &mut SmallRng) -> Vec<ObjectiveState> {
        (1..=6)
            .map(|i| ObjectiveState {
                id: format!("OBJ-{i}"),
                lat: rng.gen_range(-8.0..8.0),
                lng: rng.gen_range(32.0..58.0),
                control: ObjControl::Neutral,
            })
            .collect()
    }

    /// Run the deterministic turn resolver, mutating the force states and
    /// returning a list of events to emit.
    fn resolve_turn(
        run_id: &str,
        turn: i32,
        run: &mut RunRuntimeState,
        rng: &mut SmallRng,
    ) -> Vec<SimEvent> {
        let w_mod = weather_mod(&run.config.weather_preset);
        let t_mod = terrain_mod(&run.config.terrain_preset);

        let mut events = Vec::new();

        // ── Supply drain every turn ──────────────────────────────────────────
        let drain_base = 0.06;
        let drain_weather_penalty = (1.0 - w_mod) * 0.02;
        let drain = drain_base + drain_weather_penalty;

        for u in &mut run.blue.units {
            u.ammo = (u.ammo - drain * 1.1).max(0.0);
            u.fuel = (u.fuel - drain * 0.9).max(0.0);
        }
        for u in &mut run.red.units {
            u.ammo = (u.ammo - drain * 1.0).max(0.0);
            u.fuel = (u.fuel - drain * 0.85).max(0.0);
        }

        // Emit one SUPPLY_CONSUMED event per side
        events.push(Self::supply_event(run_id, turn, rng, "BLUE"));
        events.push(Self::supply_event(run_id, turn, rng, "RED"));

        // ── Unit movements ───────────────────────────────────────────────────
        // Move 1–3 blue units and 1–2 red units per turn.
        let blue_movers = rng.gen_range(1..=std::cmp::min(3, run.blue.units.len().max(1)));
        for idx in 0..blue_movers {
            if let Some(u) = run.blue.units.get_mut(idx) {
                u.lat += rng.gen_range(-0.5..0.5);
                u.lng += rng.gen_range(-0.5..0.5);
                events.push(SimEvent {
                    run_id: run_id.to_string(),
                    timestamp_ms: Self::now_ms(),
                    turn_number: turn,
                    r#type: EventType::UnitMove as i32,
                    entity_id: Uuid::new_v4().to_string(),
                    location: Some(GeoPoint { lat: u.lat, lng: u.lng }),
                    payload: serde_json::to_vec(&serde_json::json!({"turn": turn, "side": "BLUE"}))
                        .unwrap_or_default(),
                });
            }
        }

        // ── Engagement resolution ────────────────────────────────────────────
        // 1 engagement per turn; outcome driven by force ratio + modifiers.
        let blue_eff = run.blue.strength_pct() * w_mod;
        let red_eff = run.red.strength_pct() * t_mod; // terrain favours defender
        let ratio = if red_eff < 0.001 { 10.0 } else { blue_eff / red_eff };

        let (blue_cas, red_cas) = if ratio > 2.0 {
            (rng.gen_range(0..15_i32), rng.gen_range(20..60_i32))
        } else if ratio > 1.2 {
            (rng.gen_range(5..25_i32), rng.gen_range(15..45_i32))
        } else if ratio > 0.8 {
            (rng.gen_range(10..35_i32), rng.gen_range(10..35_i32))
        } else {
            (rng.gen_range(20..60_i32), rng.gen_range(0..15_i32))
        };

        let outcome = if ratio > 3.0 {
            "decisive_attacker_victory"
        } else if ratio > 1.5 {
            "attacker_victory"
        } else if ratio > 0.8 {
            "contested"
        } else {
            "defender_victory"
        };

        // Apply attrition to units (proportional to casualties / initial strength)
        let blue_init = run.blue.units.len().max(1) as f64 * 150.0;
        let red_init = run.red.units.len().max(1) as f64 * 150.0;
        for u in &mut run.blue.units {
            u.strength = (u.strength - blue_cas as f64 / blue_init).max(0.0);
        }
        for u in &mut run.red.units {
            u.strength = (u.strength - red_cas as f64 / red_init).max(0.0);
        }
        run.blue.total_kia += blue_cas;
        run.blue.total_wia += (blue_cas as f64 * 2.3) as i32;
        run.red.total_kia += red_cas;
        run.red.total_wia += (red_cas as f64 * 2.3) as i32;

        let eng_lat = rng.gen_range(-8.0..8.0);
        let eng_lng = rng.gen_range(32.0..58.0);
        let eng_payload = serde_json::to_vec(&serde_json::json!({
            "turn": turn,
            "blue_casualties": blue_cas,
            "red_casualties": red_cas,
            "atk_score": blue_eff,
            "def_score": red_eff,
            "ratio": ratio,
            "outcome": outcome,
        }))
        .unwrap_or_default();
        events.push(SimEvent {
            run_id: run_id.to_string(),
            timestamp_ms: Self::now_ms(),
            turn_number: turn,
            r#type: EventType::Engagement as i32,
            entity_id: Uuid::new_v4().to_string(),
            location: Some(GeoPoint { lat: eng_lat, lng: eng_lng }),
            payload: eng_payload,
        });

        // CASUALTY event when losses are significant
        if blue_cas + red_cas > 20 {
            events.push(SimEvent {
                run_id: run_id.to_string(),
                timestamp_ms: Self::now_ms(),
                turn_number: turn,
                r#type: EventType::Casualty as i32,
                entity_id: Uuid::new_v4().to_string(),
                location: Some(GeoPoint { lat: eng_lat, lng: eng_lng }),
                payload: serde_json::to_vec(&serde_json::json!({
                    "turn": turn,
                    "blue_casualties": blue_cas,
                    "red_casualties": red_cas,
                }))
                .unwrap_or_default(),
            });
        }

        // ── Equipment losses (once every ~3 turns) ───────────────────────────
        if turn % 3 == 0 {
            run.blue.armor_losses += rng.gen_range(0..3);
            run.blue.arty_losses += rng.gen_range(0..2);
            run.red.armor_losses += rng.gen_range(0..3);
            run.red.arty_losses += rng.gen_range(0..2);
        }

        // ── Airstrike (probabilistic, ~40% chance per turn) ──────────────────
        if rng.gen_bool(0.40) {
            let side = if rng.gen_bool(0.5) { "BLUE" } else { "RED" };
            let a_lat = rng.gen_range(-8.0..8.0);
            let a_lng = rng.gen_range(32.0..58.0);
            if side == "BLUE" {
                run.blue.air_losses += rng.gen_range(0..2);
            } else {
                run.red.air_losses += rng.gen_range(0..2);
            }
            events.push(SimEvent {
                run_id: run_id.to_string(),
                timestamp_ms: Self::now_ms(),
                turn_number: turn,
                r#type: EventType::Airstrike as i32,
                entity_id: Uuid::new_v4().to_string(),
                location: Some(GeoPoint { lat: a_lat, lng: a_lng }),
                payload: serde_json::to_vec(&serde_json::json!({"turn": turn, "side": side}))
                    .unwrap_or_default(),
            });
        }

        // ── Resupply (probabilistic, ~30% chance per turn) ───────────────────
        if rng.gen_bool(0.30) {
            let side = if rng.gen_bool(0.5) { "BLUE" } else { "RED" };
            let ammo_r: f64 = rng.gen_range(0.10..0.25);
            let fuel_r: f64 = rng.gen_range(0.10..0.20);
            let rats_r: f64 = rng.gen_range(0.05..0.15);
            // Apply resupply to units
            let units = if side == "BLUE" { &mut run.blue.units } else { &mut run.red.units };
            for u in units.iter_mut() {
                u.ammo = (u.ammo + ammo_r).min(1.0);
                u.fuel = (u.fuel + fuel_r).min(1.0);
            }
            events.push(SimEvent {
                run_id: run_id.to_string(),
                timestamp_ms: Self::now_ms(),
                turn_number: turn,
                r#type: EventType::Resupply as i32,
                entity_id: Uuid::new_v4().to_string(),
                location: Some(GeoPoint {
                    lat: rng.gen_range(-8.0..8.0),
                    lng: rng.gen_range(32.0..58.0),
                }),
                payload: serde_json::to_vec(&serde_json::json!({
                    "turn": turn,
                    "side": side,
                    "ammo_restored": ammo_r,
                    "fuel_restored": fuel_r,
                    "rations_restored": rats_r,
                }))
                .unwrap_or_default(),
            });
        }

        // ── Objective contest (~25% chance per objective per turn) ───────────
        for obj in &mut run.objectives {
            if rng.gen_bool(0.25) {
                let winner = if rng.gen_bool(0.5) {
                    ObjControl::Blue
                } else {
                    ObjControl::Red
                };
                let side_str = match &winner {
                    ObjControl::Blue => "BLUE",
                    ObjControl::Red => "RED",
                    ObjControl::Neutral => "CONTESTED",
                };
                // Update objective counts
                match &obj.control {
                    ObjControl::Blue => run.blue.objectives_held -= 1,
                    ObjControl::Red => run.red.objectives_held -= 1,
                    ObjControl::Neutral => {}
                }
                match &winner {
                    ObjControl::Blue => run.blue.objectives_held += 1,
                    ObjControl::Red => run.red.objectives_held += 1,
                    ObjControl::Neutral => {}
                }
                obj.control = winner;
                events.push(SimEvent {
                    run_id: run_id.to_string(),
                    timestamp_ms: Self::now_ms(),
                    turn_number: turn,
                    r#type: EventType::ObjectiveCaptured as i32,
                    entity_id: Uuid::new_v4().to_string(),
                    location: Some(GeoPoint { lat: obj.lat, lng: obj.lng }),
                    payload: serde_json::to_vec(&serde_json::json!({
                        "turn": turn,
                        "objective": obj.id,
                        "side": side_str,
                    }))
                    .unwrap_or_default(),
                });
            }
        }

        events
    }

    fn supply_event(run_id: &str, turn: i32, rng: &mut SmallRng, side: &str) -> SimEvent {
        SimEvent {
            run_id: run_id.to_string(),
            timestamp_ms: Self::now_ms(),
            turn_number: turn,
            r#type: EventType::SupplyConsumed as i32,
            entity_id: Uuid::new_v4().to_string(),
            location: Some(GeoPoint {
                lat: rng.gen_range(-8.0..8.0),
                lng: rng.gen_range(32.0..58.0),
            }),
            payload: serde_json::to_vec(&serde_json::json!({"turn": turn, "side": side}))
                .unwrap_or_default(),
        }
    }
}

type EventStream = Pin<Box<dyn Stream<Item = Result<SimEvent, Status>> + Send + 'static>>;

#[tonic::async_trait]
impl SimEngine for SimEngineService {
    type RunScenarioStream = EventStream;

    async fn run_scenario(
        &self,
        request: Request<SimRequest>,
    ) -> Result<Response<Self::RunScenarioStream>, Status> {
        let req = request.into_inner();
        let run_id = if req.run_id.is_empty() {
            Uuid::new_v4().to_string()
        } else {
            req.run_id
        };
        let cfg = req.config.unwrap_or(ScenarioConfig {
            mode: "turn_based".to_string(),
            blue_force_ids: vec![],
            red_force_ids: vec![],
            theater_bounds_json: "{}".to_string(),
            start_time_iso: "".to_string(),
            duration_hours: 24,
            monte_carlo_runs: 1000,
            weather_preset: "clear".to_string(),
            terrain_preset: "flat".to_string(),
            fog_of_war: true,
            terrain_effects: true,
            seed: 0,
        });

        let total_turns = SimEngineService::turns_from_config(&cfg);

        // Derive seed: use config.seed if provided, otherwise hash the run_id
        let base_seed = if cfg.seed != 0 {
            cfg.seed as u64
        } else {
            SimEngineService::seed_from_run_id(&run_id)
        };
        let mut rng = SmallRng::seed_from_u64(base_seed);

        let blue_force = SimEngineService::init_force(&cfg.blue_force_ids, &mut rng);
        let red_force = SimEngineService::init_force(&cfg.red_force_ids, &mut rng);
        let objectives = SimEngineService::init_objectives(&mut rng);

        {
            let mut runs = self.state.runs.write().await;
            runs.insert(
                run_id.clone(),
                RunRuntimeState {
                    status: "running".to_string(),
                    progress: 0.0,
                    turn_number: 0,
                    total_turns,
                    config: cfg.clone(),
                    blue: blue_force,
                    red: red_force,
                    objectives,
                    snapshots: HashMap::new(),
                },
            );
        }

        let (tx, rx) = tokio::sync::mpsc::channel::<Result<SimEvent, Status>>(32);
        let state = self.state.clone();
        let run_id_for_task = run_id.clone();

        tokio::spawn(async move {
            // Re-derive RNG from the same seed for the turn loop
            let mut rng = SmallRng::seed_from_u64(base_seed);

            for turn in 1..=total_turns {
                // Check for pause
                loop {
                    let paused = {
                        let runs = state.runs.read().await;
                        runs.get(&run_id_for_task)
                            .map(|r| r.status == "paused")
                            .unwrap_or(false)
                    };
                    if !paused {
                        break;
                    }
                    sleep(Duration::from_millis(200)).await;
                }

                let events = {
                    let mut runs = state.runs.write().await;
                    if let Some(run) = runs.get_mut(&run_id_for_task) {
                        run.turn_number = turn;
                        run.progress = turn as f64 / total_turns as f64;
                        let evts = SimEngineService::resolve_turn(
                            &run_id_for_task,
                            turn,
                            run,
                            &mut rng,
                        );
                        // Store snapshot for this turn
                        let snap = run.build_sim_state(&run_id_for_task);
                        run.snapshots.insert(turn, snap);
                        evts
                    } else {
                        break;
                    }
                };

                for evt in events {
                    if tx.send(Ok(evt)).await.is_err() {
                        return;
                    }
                }
                sleep(Duration::from_millis(120)).await;
            }

            let mut runs = state.runs.write().await;
            if let Some(run) = runs.get_mut(&run_id_for_task) {
                run.status = "complete".to_string();
                run.progress = 1.0;
            }
        });

        let stream: Self::RunScenarioStream = Box::pin(ReceiverStream::new(rx));
        Ok(Response::new(stream))
    }

    async fn pause_run(&self, request: Request<RunRef>) -> Result<Response<RunStatus>, Status> {
        let run_id = request.into_inner().run_id;
        let mut runs = self.state.runs.write().await;
        let run = runs
            .get_mut(&run_id)
            .ok_or_else(|| Status::not_found("run not found"))?;
        run.status = "paused".to_string();

        Ok(Response::new(RunStatus {
            run_id,
            status: run.status.clone(),
            progress: run.progress,
            message: "run paused".to_string(),
        }))
    }

    async fn resume_run(&self, request: Request<RunRef>) -> Result<Response<RunStatus>, Status> {
        let run_id = request.into_inner().run_id;
        let mut runs = self.state.runs.write().await;
        let run = runs
            .get_mut(&run_id)
            .ok_or_else(|| Status::not_found("run not found"))?;
        run.status = "running".to_string();

        Ok(Response::new(RunStatus {
            run_id,
            status: run.status.clone(),
            progress: run.progress,
            message: "run resumed".to_string(),
        }))
    }

    async fn step_turn(&self, request: Request<RunRef>) -> Result<Response<SimEvent>, Status> {
        let run_id = request.into_inner().run_id;
        let mut runs = self.state.runs.write().await;
        let run = runs
            .get_mut(&run_id)
            .ok_or_else(|| Status::not_found("run not found"))?;

        run.turn_number += 1;
        run.progress = (run.turn_number as f64 / run.total_turns as f64).min(1.0);
        if run.progress >= 1.0 {
            run.status = "complete".to_string();
        }

        let seed = SimEngineService::seed_from_run_id(&run_id)
            .wrapping_add(run.turn_number as u64 * 0x9e37_79b9_7f4a_7c15);
        let mut rng = SmallRng::seed_from_u64(seed);

        let mut events =
            SimEngineService::resolve_turn(&run_id, run.turn_number, run, &mut rng);
        let snap = run.build_sim_state(&run_id);
        run.snapshots.insert(run.turn_number, snap);

        // Return the first meaningful event (engagement if present, else first event)
        let evt = events
            .iter()
            .position(|e| e.r#type == EventType::Engagement as i32)
            .map(|i| events.remove(i))
            .unwrap_or_else(|| {
                if events.is_empty() {
                    SimEvent {
                        run_id: run_id.to_string(),
                        timestamp_ms: SimEngineService::now_ms(),
                        turn_number: run.turn_number,
                        r#type: EventType::PhaseChange as i32,
                        entity_id: Uuid::new_v4().to_string(),
                        location: None,
                        payload: serde_json::to_vec(&serde_json::json!({"turn": run.turn_number}))
                            .unwrap_or_default(),
                    }
                } else {
                    events.remove(0)
                }
            });

        Ok(Response::new(evt))
    }

    async fn get_state(&self, request: Request<RunRef>) -> Result<Response<SimState>, Status> {
        let run_id = request.into_inner().run_id;
        let runs = self.state.runs.read().await;
        let run = runs
            .get(&run_id)
            .ok_or_else(|| Status::not_found("run not found"))?;

        Ok(Response::new(run.build_sim_state(&run_id)))
    }

    async fn inject_event(
        &self,
        request: Request<EventInjection>,
    ) -> Result<Response<Ack>, Status> {
        let req = request.into_inner();
        let runs = self.state.runs.read().await;
        if !runs.contains_key(&req.run_id) {
            return Err(Status::not_found("run not found"));
        }
        Ok(Response::new(Ack {
            ok: true,
            message: "event accepted".to_string(),
        }))
    }

    async fn get_checkpoint(
        &self,
        request: Request<RunRef>,
    ) -> Result<Response<SimState>, Status> {
        let req = request.into_inner();
        let run_id = req.run_id;
        let turn = req.turn;
        let runs = self.state.runs.read().await;
        let run = runs
            .get(&run_id)
            .ok_or_else(|| Status::not_found("run not found"))?;

        if turn == 0 {
            // Latest snapshot
            let latest = run.snapshots.keys().max().copied().unwrap_or(0);
            if latest == 0 {
                return Ok(Response::new(run.build_sim_state(&run_id)));
            }
            return run
                .snapshots
                .get(&latest)
                .cloned()
                .map(Response::new)
                .ok_or_else(|| Status::not_found("snapshot not found"));
        }

        run.snapshots
            .get(&turn)
            .cloned()
            .map(Response::new)
            .ok_or_else(|| Status::not_found(format!("snapshot for turn {turn} not found")))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt()
        .with_env_filter(
            std::env::var("RUST_LOG")
                .unwrap_or_else(|_| "sim_engine=info,tower=warn,tonic=warn".to_string()),
        )
        .init();

    let host = std::env::var("SIM_ENGINE_HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
    let port = std::env::var("SIM_ENGINE_PORT").unwrap_or_else(|_| "50051".to_string());
    let addr = format!("{}:{}", host, port).parse()?;

    info!("sim-engine gRPC listening on {}", addr);

    let service = SimEngineService::default();
    Server::builder()
        .add_service(SimEngineServer::new(service))
        .serve(addr)
        .await?;

    Ok(())
}