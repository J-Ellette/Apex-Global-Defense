use std::collections::HashMap;
use std::pin::Pin;
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};

use rand::Rng;
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
    Ack, EventInjection, EventType, GeoPoint, RunRef, RunStatus, ScenarioConfig, SimEvent, SimRequest, SimState,
};

#[derive(Clone, Debug)]
struct RunRuntimeState {
    status: String,
    progress: f64,
    turn_number: i32,
    config: Option<ScenarioConfig>,
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
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default();
        now.as_millis() as i64
    }

    fn turns_from_config(cfg: &ScenarioConfig) -> i32 {
        let hours = if cfg.duration_hours <= 0 { 24 } else { cfg.duration_hours };
        std::cmp::max(1, hours / 4)
    }

    fn make_event(run_id: &str, turn: i32) -> SimEvent {
        let mut rng = rand::thread_rng();
        let event_type = match rng.gen_range(0..=6) {
            0 => EventType::UnitMove,
            1 => EventType::Engagement,
            2 => EventType::Casualty,
            3 => EventType::SupplyConsumed,
            4 => EventType::ObjectiveCaptured,
            5 => EventType::Airstrike,
            _ => EventType::Resupply,
        };

        let payload = serde_json::json!({
            "turn": turn,
            "note": "sim-engine generated event"
        });

        SimEvent {
            run_id: run_id.to_string(),
            timestamp_ms: Self::now_ms(),
            turn_number: turn,
            r#type: event_type as i32,
            entity_id: Uuid::new_v4().to_string(),
            location: Some(GeoPoint {
                lat: rng.gen_range(-10.0..10.0),
                lng: rng.gen_range(30.0..60.0),
            }),
            payload: serde_json::to_vec(&payload).unwrap_or_default(),
        }
    }

    async fn upsert_run(
        &self,
        run_id: &str,
        status: &str,
        progress: f64,
        turn_number: i32,
        config: Option<ScenarioConfig>,
    ) {
        let mut runs = self.state.runs.write().await;
        runs.insert(
            run_id.to_string(),
            RunRuntimeState {
                status: status.to_string(),
                progress,
                turn_number,
                config,
            },
        );
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
            fog_of_war: true,
            terrain_effects: true,
        });

        let total_turns = Self::turns_from_config(&cfg);
        self.upsert_run(&run_id, "running", 0.0, 0, Some(cfg.clone())).await;

        let (tx, rx) = tokio::sync::mpsc::channel::<Result<SimEvent, Status>>(16);
        let state = self.state.clone();
        let run_id_for_task = run_id.clone();

        tokio::spawn(async move {
            for turn in 1..=total_turns {
                {
                    let mut runs = state.runs.write().await;
                    if let Some(current) = runs.get_mut(&run_id_for_task) {
                        if current.status == "paused" {
                            drop(runs);
                            sleep(Duration::from_millis(200)).await;
                            continue;
                        }
                        current.turn_number = turn;
                        current.progress = (turn as f64) / (total_turns as f64);
                    }
                }

                let evt = SimEngineService::make_event(&run_id_for_task, turn);
                if tx.send(Ok(evt)).await.is_err() {
                    return;
                }
                sleep(Duration::from_millis(150)).await;
            }

            let mut runs = state.runs.write().await;
            if let Some(current) = runs.get_mut(&run_id_for_task) {
                current.status = "complete".to_string();
                current.progress = 1.0;
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
        let total_turns = run
            .config
            .as_ref()
            .map(Self::turns_from_config)
            .unwrap_or(6);
        run.progress = (run.turn_number as f64 / total_turns as f64).min(1.0);
        if run.progress >= 1.0 {
            run.status = "complete".to_string();
        }

        let evt = Self::make_event(&run_id, run.turn_number);
        Ok(Response::new(evt))
    }

    async fn get_state(&self, request: Request<RunRef>) -> Result<Response<SimState>, Status> {
        let run_id = request.into_inner().run_id;
        let runs = self.state.runs.read().await;
        let run = runs
            .get(&run_id)
            .ok_or_else(|| Status::not_found("run not found"))?;

        let objectives = serde_json::json!({
            "OBJ-1": "CONTESTED",
            "OBJ-2": "BLUE",
            "OBJ-3": "RED"
        });

        Ok(Response::new(SimState {
            run_id,
            status: run.status.clone(),
            progress: run.progress,
            turn_number: run.turn_number,
            sim_time_ms: Self::now_ms(),
            blue_unit_count: run
                .config
                .as_ref()
                .map(|c| c.blue_force_ids.len() as i32)
                .unwrap_or(0),
            red_unit_count: run
                .config
                .as_ref()
                .map(|c| c.red_force_ids.len() as i32)
                .unwrap_or(0),
            objectives_status_json: objectives.to_string(),
        }))
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