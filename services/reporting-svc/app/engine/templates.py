from __future__ import annotations

"""Deterministic report template generators for SITREP, INTSUM, and CONOPS.

These generators produce realistic, structured report content using provided
context data (scenario name, run events, threat data) and deterministic
templates.  Each generator returns a content dict and a human-readable summary.
"""

from datetime import datetime, timedelta, timezone
from typing import Any


# ---------------------------------------------------------------------------
# SITREP Generator
# ---------------------------------------------------------------------------

def generate_sitrep(
    scenario_name: str = "EXERCISE IRON HAWK",
    run_events: list[dict] | None = None,
    logistics: dict | None = None,
    context: str | None = None,
) -> dict[str, Any]:
    """Generate a SITREP content block from simulation run data."""
    now = datetime.now(tz=timezone.utc)
    period_from = (now - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    period_to = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    events = run_events or []
    engagements = [e for e in events if e.get("event_type") == "ENGAGEMENT"]
    casualties = [e for e in events if e.get("event_type") == "CASUALTY"]
    objectives = [e for e in events if e.get("event_type") == "OBJECTIVE_CAPTURED"]
    resupply_events = [e for e in events if e.get("event_type") == "RESUPPLY"]

    sig_events = []
    for e in (engagements + objectives)[:5]:
        payload = e.get("payload", {})
        sig_events.append(
            f"{e.get('event_type', 'EVENT')}: "
            f"{payload.get('description', 'No description')} "
            f"(Turn {e.get('turn', '?')})"
        )

    blue_kia = sum(
        e.get("payload", {}).get("blue_kia", 0)
        for e in casualties
    )
    red_kia = sum(
        e.get("payload", {}).get("red_kia", 0)
        for e in casualties
    )

    log = logistics or {}
    blue_log = log.get("blue", {})
    red_log = log.get("red", {})

    content = {
        "period_from": period_from,
        "period_to": period_to,
        "situation_summary": (
            context
            or f"Operations continue in {scenario_name}. "
            f"BLUE force has conducted {len(engagements)} engagement(s) during the reporting period. "
            f"{len(objectives)} objective(s) captured."
        ),
        "friendly_forces": (
            f"BLUE FORCE: Operational strength {blue_log.get('strength_pct', 'N/A')}%. "
            f"KIA: {blue_kia}. "
            f"Ammo: {blue_log.get('supply_levels', {}).get('ammo_pct', 'N/A')}% | "
            f"Fuel: {blue_log.get('supply_levels', {}).get('fuel_pct', 'N/A')}% | "
            f"Rations: {blue_log.get('supply_levels', {}).get('rations_pct', 'N/A')}%."
        ),
        "enemy_forces": (
            f"RED FORCE: Estimated strength {red_log.get('strength_pct', 'N/A')}%. "
            f"KIA: {red_kia}. "
            f"Ammo: {red_log.get('supply_levels', {}).get('ammo_pct', 'N/A')}% | "
            f"Fuel: {red_log.get('supply_levels', {}).get('fuel_pct', 'N/A')}%."
        ),
        "civilian_situation": (
            "Civilian population impact being monitored. "
            "Humanitarian corridors remain in effect pending assessment."
        ),
        "significant_events": sig_events,
        "current_operations": (
            f"Ongoing offensive/defensive operations across {len(engagements)} contact points."
        ),
        "planned_operations": (
            f"{len(resupply_events)} RESUPPLY operation(s) scheduled. "
            "Continuation of current axis of advance pending commander decision."
        ),
        "logistics_status": (
            f"Blue supply status: Ammo {blue_log.get('supply_levels', {}).get('ammo_pct', 'N/A')}%, "
            f"Fuel {blue_log.get('supply_levels', {}).get('fuel_pct', 'N/A')}%. "
            "Resupply convoy enroute."
        ),
        "weather": "Standard conditions. No significant weather impact on operations.",
        "commander_assessment": (
            "Overall BLUE force posture is SATISFACTORY. "
            "Continued pressure recommended on RED FORCE eastern flank. "
            "Monitor logistics sustainability at current operational tempo."
        ),
        "next_report_due": (now + timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    summary = (
        f"SITREP for {scenario_name}: "
        f"{len(engagements)} engagements, {len(objectives)} objectives captured, "
        f"{blue_kia} BLUE KIA, {red_kia} RED KIA in reporting period."
    )
    return {"content": content, "summary": summary}


# ---------------------------------------------------------------------------
# INTSUM Generator
# ---------------------------------------------------------------------------

def generate_intsum(
    scenario_name: str = "EXERCISE IRON HAWK",
    intel_items: list[dict] | None = None,
    stix_indicators: list[dict] | None = None,
    threat_assessments: list[dict] | None = None,
    context: str | None = None,
) -> dict[str, Any]:
    """Generate an INTSUM content block from intelligence data."""
    now = datetime.now(tz=timezone.utc)
    period_from = (now - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    period_to = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    items = intel_items or []
    indicators = stix_indicators or []
    assessments = threat_assessments or []

    # Determine overall threat level from assessments
    threat_level = "MODERATE"
    if assessments:
        levels = {"NEGLIGIBLE": 0, "LOW": 1, "MODERATE": 2, "HIGH": 3, "CRITICAL": 4}
        max_level = max(
            levels.get(a.get("threat_level", "MODERATE"), 2)
            for a in assessments
        )
        level_map = {v: k for k, v in levels.items()}
        threat_level = level_map.get(max_level, "MODERATE")

    # Summarize key developments from intel items
    key_developments = [
        f"{item.get('title', 'Unknown item')} "
        f"[{item.get('source_type', 'OSINT')} — Reliability: {item.get('reliability', 'F')}]"
        for item in items[:5]
    ]

    # Build threat indicators list from STIX
    threat_inds = [
        {
            "indicator": ind.get("name", "Unknown"),
            "pattern_type": ind.get("pattern_type", "stix"),
            "confidence": str(ind.get("confidence", 50)),
        }
        for ind in indicators[:5]
    ]

    # ISR gaps
    isr_gaps = [
        "Limited HUMINT coverage of RED FORCE command nodes",
        "SIGINT collection degraded due to adversary emission control (EMCON)",
    ]
    if not stix_indicators:
        isr_gaps.append("No commercial threat intelligence (CTI) feeds currently integrated")

    content = {
        "period_from": period_from,
        "period_to": period_to,
        "enemy_disposition": (
            context
            or "RED FORCE maintains defensive posture along northern axis. "
            "Forward elements observed repositioning. "
            "Logistics nodes identified at grid references TF-1847 and TF-2063."
        ),
        "enemy_strength": (
            "RED FORCE estimated at 65-75% operational strength. "
            "Armor availability: 80%. Artillery degraded ~30% from counter-battery."
        ),
        "enemy_capabilities": (
            "Conventional ground forces. Limited air defense coverage. "
            "Electronic warfare assets active. Cyber operations capability assessed as MEDIUM."
        ),
        "enemy_intentions": (
            "Likely to consolidate current defensive line and seek resupply before resuming offensive action. "
            "Probability of offensive action within 48hrs: 35%."
        ),
        "threat_level": threat_level,
        "key_developments": key_developments,
        "isr_gaps": isr_gaps,
        "cyber_threats": (
            f"{len(indicators)} STIX indicator(s) active. "
            "APT activity detected targeting logistics coordination networks. "
            "MITRE ATT&CK: T1071 (C2), T1566 (Phishing) — elevated alerting recommended."
        ),
        "cbrn_threats": (
            "No confirmed CBRN use. Precautionary monitoring in effect. "
            "Chemical agent precursor movement observed (UNCONFIRMED)."
        ),
        "threat_indicators": threat_inds,
        "analyst_assessment": (
            "RED FORCE is conducting a delay operation to allow main body reconstitution. "
            "BLUE FORCE should exploit current momentum within 24-48hr window before RED resupply. "
            "Recommend surge ISR collection on western flank."
        ),
        "confidence_level": "MEDIUM",
    }

    summary = (
        f"INTSUM for {scenario_name}: Threat level {threat_level}. "
        f"{len(items)} intel items processed, {len(indicators)} STIX indicators active. "
        f"{len(isr_gaps)} ISR gap(s) identified."
    )
    return {"content": content, "summary": summary}


# ---------------------------------------------------------------------------
# CONOPS Generator
# ---------------------------------------------------------------------------

def generate_conops(
    scenario_name: str = "EXERCISE IRON HAWK",
    units: list[dict] | None = None,
    context: str | None = None,
) -> dict[str, Any]:
    """Generate a CONOPS content block."""
    forces = units or []
    n_units = len(forces)

    tasks_to_subordinates = [
        {"unit": f.get("name", f"Unit {i+1}"), "task": "Secure assigned sector; report contact immediately"}
        for i, f in enumerate(forces[:4])
    ]
    if not tasks_to_subordinates:
        tasks_to_subordinates = [
            {"unit": "1st Maneuver Brigade", "task": "Main effort — seize OBJECTIVE EAGLE along Axis BLUE"},
            {"unit": "2nd Maneuver Brigade", "task": "Supporting effort — fix RED FORCE at PHASE LINE HAWK"},
            {"unit": "Combat Aviation Brigade", "task": "Deep attack on RED FORCE artillery and C2 nodes"},
            {"unit": "Division Artillery", "task": "Suppress and neutralize RED FORCE AD systems; on-call SEAD"},
        ]

    content = {
        "mission_statement": (
            context
            or f"BLUE FORCE conducts combined arms offensive operations in {scenario_name} "
            "to defeat RED FORCE within assigned area of operations, "
            "seize key terrain, and restore freedom of movement by D+7."
        ),
        "commander_intent": (
            "PURPOSE: Defeat RED FORCE main defense and exploit to PHASE LINE FALCON. "
            "METHOD: Synchronized combined arms assault with air-ground integration. "
            "END STATE: RED FORCE rendered combat ineffective; key terrain secured; "
            "civilian population protected."
        ),
        "end_state": (
            "RED FORCE main body defeated or withdrawn beyond PHASE LINE FALCON. "
            "All named objectives seized. LOC open and secured. "
            "BLUE FORCE consolidated and prepared for follow-on operations."
        ),
        "scheme_of_maneuver": (
            "Phase 1 (D-Day to D+2): Shaping. Deep fires suppress AD and isolate RED FORCE. "
            "Phase 2 (D+2 to D+4): Breach and assault. 1st Bde conducts breach on eastern axis. "
            "2nd Bde fixes RED FORCE northern flank. "
            "Phase 3 (D+4 to D+7): Exploitation. CAB exploits deep; ground forces clear and consolidate."
        ),
        "tasks_to_subordinate_units": tasks_to_subordinates,
        "tasks_to_supporting_elements": [
            {"element": "Joint Air Operations Center", "task": "CAS on-call; 2x CAP stations; SEAD on request"},
            {"element": "Logistics Battalion", "task": "Pre-positioned Class III/V at FARP EAGLE by D+1"},
            {"element": "Engineers", "task": "Breach preparation D-Day -6hrs; route clearance on Axis BLUE"},
        ],
        "coordinating_instructions": [
            "FIRES: No-fire areas (NFA) established around refugee corridor — grid TF-1893",
            "ROE: Current ROE apply. Positive ID required before engagement",
            "EMCON: MINIMIZE posture until H-Hour",
            "COMMS: Primary — SATCOM SINCGARS; Alternate — HF manpack",
            "Resupply push package: every 12hrs at FARP EAGLE and FARP CONDOR",
        ],
        "sustainment_concept": (
            "Class I: 72hr push package. Class III: Bulk fuel at FARP EAGLE/CONDOR. "
            "Class V: Unit basic load + 2 resupply lifts. "
            "MEDEVAC: 9-line procedures; two MEDEVAC UH-60 on strip alert."
        ),
        "command_and_signal": (
            "Main CP: GRID TF-2104. TAC CP: Mobile. "
            "Commander: Call sign IRON SIX. "
            "Succession of command: DCO → COS → G3."
        ),
        "risk_assessment": (
            "HIGH: CBRN threat in sector — protective measures in effect. "
            "MEDIUM: Civilian population displacement risk — CA teams attached to lead elements. "
            "MEDIUM: Supply line exposure to enemy interdiction — armed escort required."
        ),
        "execution_phases": [
            {"phase": "Phase 1 — Shaping", "duration": "D-Day to D+2", "description": "Deep fires; ISR surge; breach prep"},
            {"phase": "Phase 2 — Assault", "duration": "D+2 to D+4", "description": "Combined arms breach; main effort attack"},
            {"phase": "Phase 3 — Exploitation", "duration": "D+4 to D+7", "description": "Deep exploitation; consolidation; transition to defense"},
        ],
    }

    summary = (
        f"CONOPS for {scenario_name}: 3-phase combined arms operation. "
        f"{n_units or 4} subordinate unit tasks assigned. "
        "Estimated D+7 mission completion."
    )
    return {"content": content, "summary": summary}
