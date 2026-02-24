"""Deterministic civilian impact model.

Given a list of simulation events and a list of population zones,
computes per-zone civilian casualties, wounded, displaced persons,
and infrastructure damage.

Model logic:
- ENGAGEMENT events near a zone cause casualties proportional to
  zone population, density class, and event severity
- AIRSTRIKE events cause higher casualties and more displacement
- CBRN_RELEASE events cause mass casualties and mass displacement
- CASUALTY events add directly to civilian wounded count (collateral)
- Each zone has a base displacement fraction that scales with total damage
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any

from app.models import (
    DensityClass,
    ImpactAssessment,
    ZoneImpact,
)

# Density multipliers for casualties
DENSITY_MULT = {
    DensityClass.URBAN: 1.0,
    DensityClass.SUBURBAN: 0.4,
    DensityClass.RURAL: 0.1,
    DensityClass.SPARSE: 0.02,
}

# Event type severity (casualty rate per 1000 population within radius)
EVENT_SEVERITY = {
    "ENGAGEMENT": 0.8,
    "AIRSTRIKE": 2.5,
    "CBRN_RELEASE": 8.0,
    "CASUALTY": 0.3,
    "NAVAL_ACTION": 0.5,
    "CYBER_ATTACK": 0.0,
    "UNIT_MOVE": 0.0,
    "SUPPLY_CONSUMED": 0.0,
    "RESUPPLY": 0.0,
    "OBJECTIVE_CAPTURED": 0.15,
    "PHASE_CHANGE": 0.0,
}

# Displacement fraction (fraction of casualties that are displaced)
DISPLACEMENT_MULT = {
    "ENGAGEMENT": 5.0,
    "AIRSTRIKE": 10.0,
    "CBRN_RELEASE": 20.0,
    "CASUALTY": 2.0,
    "NAVAL_ACTION": 3.0,
    "OBJECTIVE_CAPTURED": 8.0,
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in km between two lat/lon points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_impact(
    run_id: uuid.UUID,
    scenario_id: uuid.UUID | None,
    zones: list[dict],
    events: list[dict[str, Any]],
) -> ImpactAssessment:
    """Compute civilian impact for a simulation run.

    Args:
        run_id: Simulation run UUID
        scenario_id: Scenario UUID (optional)
        zones: List of population zone dicts (id, name, latitude, longitude, radius_km,
               population, density_class)
        events: List of sim event dicts (event_type, location={lat, lng}, payload)

    Returns:
        ImpactAssessment with per-zone breakdown and totals
    """
    zone_impacts: list[ZoneImpact] = []
    total_casualties = 0
    total_wounded = 0
    total_displaced = 0

    for zone in zones:
        z_lat = float(zone["latitude"])
        z_lon = float(zone["longitude"])
        z_rad = float(zone["radius_km"])
        z_pop = int(zone["population"])
        density = DensityClass(zone["density_class"])
        density_m = DENSITY_MULT[density]

        z_casualties = 0
        z_wounded = 0
        z_displaced = 0
        z_damage = 0.0

        for event in events:
            loc = event.get("location") or {}
            if not loc:
                continue
            e_lat = float(loc.get("lat", 0.0))
            e_lon = float(loc.get("lng", 0.0) or loc.get("lon", 0.0))
            dist_km = _haversine_km(z_lat, z_lon, e_lat, e_lon)

            # Only events within 3× zone radius are relevant
            if dist_km > z_rad * 3:
                continue

            # Proximity factor: 1.0 at center, 0 at 3× radius
            prox = max(0.0, 1.0 - dist_km / (z_rad * 3))
            et = event.get("event_type", "")
            severity = EVENT_SEVERITY.get(et, 0.0)
            disp_m = DISPLACEMENT_MULT.get(et, 0.0)

            # Casualties per 1000 pop
            cas = int(z_pop * severity * density_m * prox / 1000)
            wnd = max(0, int(cas * 2.5))  # wounded ~ 2.5× killed
            dsp = int(z_pop * disp_m * density_m * prox / 1000)
            dmg = min(1.0, severity * prox * density_m * 0.15)

            z_casualties += cas
            z_wounded += wnd
            z_displaced += dsp
            z_damage = min(1.0, z_damage + dmg)

        impact_score = min(10.0, (z_casualties + z_wounded / 3 + z_displaced / 10) / max(1, z_pop / 1000))

        zone_impacts.append(
            ZoneImpact(
                zone_id=uuid.UUID(str(zone["id"])),
                zone_name=zone["name"],
                civilian_casualties=z_casualties,
                civilian_wounded=z_wounded,
                displaced_persons=z_displaced,
                infrastructure_damage_pct=round(z_damage, 3),
                impact_score=round(impact_score, 2),
            )
        )
        total_casualties += z_casualties
        total_wounded += z_wounded
        total_displaced += z_displaced

    return ImpactAssessment(
        id=uuid.uuid4(),
        run_id=run_id,
        scenario_id=scenario_id,
        assessed_at=datetime.now(timezone.utc),
        total_civilian_casualties=total_casualties,
        total_civilian_wounded=total_wounded,
        total_displaced_persons=total_displaced,
        zone_impacts=zone_impacts,
        methodology="deterministic",
    )
