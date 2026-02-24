from __future__ import annotations

"""
Gaussian Plume Dispersion Model
================================
Implements a simplified steady-state Gaussian plume equation for
CBRN hazard estimation.  This is a physics-based stub that uses
Pasquill-Gifford dispersion coefficients — conceptually equivalent
to what HYSPLIT uses for short-range transport at ground level.

Reference:
  Turner, D.B. (1994). Workbook on Atmospheric Dispersion Estimates.
  Lewis Publishers.  EPA AP-42 / EPA AERMOD guidance.

All units are SI unless otherwise stated.
"""

import math
from typing import Sequence

import numpy as np

from app.models import (
    CBRNAgent,
    CBRNRelease,
    CasualtyZone,
    ConcentrationPoint,
    DispersionSimulation,
    PlumeContour,
    StabilityClass,
)
from datetime import datetime, timezone
from uuid import uuid4


# ---------------------------------------------------------------------------
# Pasquill-Gifford σ coefficients (rural)
# σy = a · x^b   σz = c · x^d + f   (x in km, σ in m)
# ---------------------------------------------------------------------------

# (a, b) for σy
_SY_PARAMS: dict[StabilityClass, tuple[float, float]] = {
    StabilityClass.A: (0.22, 0.894),
    StabilityClass.B: (0.16, 0.894),
    StabilityClass.C: (0.11, 0.894),
    StabilityClass.D: (0.08, 0.894),
    StabilityClass.E: (0.06, 0.894),
    StabilityClass.F: (0.04, 0.894),
}

# (c, d, f) for σz
_SZ_PARAMS: dict[StabilityClass, tuple[float, float, float]] = {
    StabilityClass.A: (0.20,  0.894, 0.0),
    StabilityClass.B: (0.12,  0.894, 0.0),
    StabilityClass.C: (0.08,  0.894, 0.0),
    StabilityClass.D: (0.06,  0.894, 0.0),
    StabilityClass.E: (0.03,  0.894, 0.0),
    StabilityClass.F: (0.016, 0.894, 0.0),
}

# Maximum σz cap (m) — prevents unrealistic spread in very stable conditions
_SZ_MAX = 5000.0


def _sigma_y(x_km: float, cls: StabilityClass) -> float:
    """Horizontal dispersion coefficient σy (metres) at downwind dist x_km."""
    a, b = _SY_PARAMS[cls]
    return a * (x_km ** b) * 1000.0  # convert km→m scale factor built into Pasquill tables


def _sigma_z(x_km: float, cls: StabilityClass) -> float:
    """Vertical dispersion coefficient σz (metres)."""
    c, d, f = _SZ_PARAMS[cls]
    sz = c * (x_km ** d) * 1000.0 + f
    return min(sz, _SZ_MAX)


def _ground_concentration(
    Q_g_s: float,
    x_m: float,
    y_m: float,
    H_m: float,
    u_ms: float,
    cls: StabilityClass,
    mixing_height_m: float,
) -> float:
    """
    Ground-level concentration (mg/m³) at (x, y) from a continuous point source.

    Q_g_s   : source emission rate (g/s)
    x_m     : downwind distance (m)
    y_m     : crosswind distance (m)
    H_m     : effective release height (m)
    u_ms    : wind speed (m/s)
    cls     : Pasquill-Gifford stability class
    mixing_height_m : atmospheric mixing layer height (m)
    """
    if x_m <= 0.0:
        return 0.0

    x_km = x_m / 1000.0
    sy = _sigma_y(x_km, cls)
    sz = _sigma_z(x_km, cls)

    # Reflect off mixing layer top (first reflection only)
    denom = 2.0 * math.pi * sy * sz * u_ms
    if denom == 0.0:
        return 0.0

    crosswind = math.exp(-0.5 * (y_m / sy) ** 2)
    vertical = math.exp(-0.5 * ((0.0 - H_m) / sz) ** 2) + math.exp(
        -0.5 * ((0.0 + H_m) / sz) ** 2
    )
    # Reflection off mixing height
    if mixing_height_m > 0 and sz < 0.47 * mixing_height_m:
        pass  # No reflection needed yet
    elif mixing_height_m > 0:
        # Uniform vertical mixing assumption
        if 2.0 * math.sqrt(2.0 * math.pi) * sz >= mixing_height_m:
            # Fully mixed
            vertical = 1.0 / mixing_height_m
            denom = math.sqrt(2.0 * math.pi) * sy * u_ms

    # Convert g/m³ → mg/m³
    c_g_m3 = (Q_g_s / denom) * crosswind * vertical
    return max(c_g_m3 * 1000.0, 0.0)


def _emission_rate_g_s(release: CBRNRelease) -> float:
    """Convert release quantity + duration to steady-state emission rate (g/s)."""
    duration_s = release.duration_min * 60.0
    return (release.quantity_kg * 1000.0) / duration_s  # kg → g, /s


def _effective_height(release: CBRNRelease) -> float:
    """Effective release height (m).  Simple plume rise placeholder."""
    return release.release_height_m


def _latlon_offset(
    lat0: float,
    lon0: float,
    x_m: float,  # downwind (north-ish → rotated by wind direction)
    y_m: float,  # crosswind
    wind_dir_deg: float,
) -> tuple[float, float]:
    """
    Compute (lat, lon) for a point displaced (x_m, y_m) from origin.
    Wind direction is meteorological: wind FROM this bearing.
    Plume travels TOWARD wind_dir_deg + 180.
    """
    # Direction plume travels (degrees true)
    travel_deg = (wind_dir_deg + 180.0) % 360.0
    travel_rad = math.radians(travel_deg)

    # Unit vectors (East, North) for downwind and crosswind
    # downwind: along travel direction
    dx_east = math.sin(travel_rad) * x_m + math.cos(travel_rad) * y_m
    dx_north = math.cos(travel_rad) * x_m - math.sin(travel_rad) * y_m

    # Convert metres to degrees
    d_lat = dx_north / 111_320.0
    d_lon = dx_east / (111_320.0 * math.cos(math.radians(lat0)))

    return lat0 + d_lat, lon0 + d_lon


# ---------------------------------------------------------------------------
# Threshold helpers
# ---------------------------------------------------------------------------

def _concentration_threshold(agent: CBRNAgent, level: str) -> float | None:
    """
    Return ground-level concentration threshold (mg/m³) for a hazard level.
    We convert dose (mg·min/m³) to concentration using the release duration.
    """
    # For chemical agents we use Ct thresholds ÷ exposure_min ≈ concentration
    # For bio/rad/nuc we use approximations.
    if level == "lethal":
        if agent.lct50_mg_min_m3 is not None:
            return agent.lct50_mg_min_m3 / 10.0  # 10-min exposure
        if agent.lethal_dose_gy is not None:
            # Approximate: 1 Gy ≈ 1 mGy/min for 1000 min → use 0.1 Gy/min baseline
            return agent.lethal_dose_gy * 0.1  # mg equivalent
    elif level == "incapacitating":
        if agent.ict50_mg_min_m3 is not None:
            return agent.ict50_mg_min_m3 / 10.0
        if agent.incapacitating_dose_gy is not None:
            return agent.incapacitating_dose_gy * 0.1
    elif level == "idlh":
        if agent.idlh_mg_m3 is not None:
            return agent.idlh_mg_m3
    return None


# ---------------------------------------------------------------------------
# Plume contour builder
# ---------------------------------------------------------------------------

def _build_contour(
    release: CBRNRelease,
    agent: CBRNAgent,
    Q_g_s: float,
    H_m: float,
    threshold_mg_m3: float,
    level_label: str,
    cls: StabilityClass,
) -> tuple[PlumeContour | None, float, float]:
    """
    Sweep downwind distances to find the plume boundary where
    concentration >= threshold_mg_m3.

    Returns (PlumeContour | None, max_downwind_km, max_halfwidth_km).
    """
    u = release.met.wind_speed_ms
    mix_h = release.met.mixing_height_m

    # Scan x from 10m to 200km in logarithmic steps
    x_values = np.logspace(np.log10(10.0), np.log10(200_000.0), num=300)

    # For each x, find crosswind half-width where C >= threshold
    right_side: list[tuple[float, float]] = []  # (x_m, y_m)
    left_side: list[tuple[float, float]] = []

    max_x = 0.0
    max_hw = 0.0

    for x_m in x_values:
        # Centre-line concentration
        c_centre = _ground_concentration(Q_g_s, x_m, 0.0, H_m, u, cls, mix_h)
        if c_centre < threshold_mg_m3:
            if max_x > 0.0:
                break  # Plume has dropped below threshold; stop scanning
            continue

        max_x = x_m

        # Binary search for crosswind half-width
        y_lo, y_hi = 0.0, x_m  # upper bound: plume can't be wider than it is long
        for _ in range(20):
            y_mid = (y_lo + y_hi) / 2.0
            c = _ground_concentration(Q_g_s, x_m, y_mid, H_m, u, cls, mix_h)
            if c >= threshold_mg_m3:
                y_lo = y_mid
            else:
                y_hi = y_mid
        hw = y_lo
        max_hw = max(max_hw, hw)

        right_side.append((x_m, hw))
        left_side.append((x_m, -hw))

    if not right_side:
        return None, 0.0, 0.0

    # Build polygon: right side (downwind), then left side reversed
    polygon_points: list[list[float]] = []

    # Add release point (apex)
    polygon_points.append([release.longitude, release.latitude])

    for x_m, y_m in right_side:
        lat, lon = _latlon_offset(
            release.latitude, release.longitude,
            x_m, y_m, release.met.wind_direction_deg,
        )
        polygon_points.append([lon, lat])

    for x_m, y_m in reversed(left_side):
        lat, lon = _latlon_offset(
            release.latitude, release.longitude,
            x_m, y_m, release.met.wind_direction_deg,
        )
        polygon_points.append([lon, lat])

    # Close the ring
    polygon_points.append(polygon_points[0])

    contour = PlumeContour(
        level_mg_m3=threshold_mg_m3,
        label=level_label,
        coordinates=polygon_points,
    )
    return contour, max_x / 1000.0, max_hw / 1000.0


# ---------------------------------------------------------------------------
# Casualty estimation
# ---------------------------------------------------------------------------

def _estimate_casualties(
    area_km2: float,
    population_density: float,
    fraction_affected: float,
) -> int:
    """Simple area × density × fraction model."""
    pop_at_risk = area_km2 * population_density
    return max(0, round(pop_at_risk * fraction_affected))


def _zone_area(max_downwind_km: float, max_crosswind_km: float) -> float:
    """Approximate plume zone area as an ellipse (π·a·b)."""
    return math.pi * max_downwind_km * max_crosswind_km


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_dispersion(release: CBRNRelease, agent: CBRNAgent) -> DispersionSimulation:
    """
    Run a Gaussian plume dispersion simulation for a CBRN release event.
    Returns a DispersionSimulation with plume contours and casualty estimates.
    """
    Q_g_s = _emission_rate_g_s(release)
    H_m = _effective_height(release)
    cls = StabilityClass(release.met.stability_class)

    contours: list[PlumeContour] = []
    lethal_zone: CasualtyZone | None = None
    injury_zone: CasualtyZone | None = None
    idlh_zone: CasualtyZone | None = None

    overall_max_x = 0.0
    overall_max_hw = 0.0

    # Compute lethal contour
    thr_lethal = _concentration_threshold(agent, "lethal")
    if thr_lethal is not None:
        contour, max_x, max_hw = _build_contour(
            release, agent, Q_g_s, H_m, thr_lethal, "Lethal Zone", cls
        )
        if contour is not None:
            contours.append(contour)
            area = _zone_area(max_x, max_hw)
            lethal_zone = CasualtyZone(
                label="Lethal Zone",
                estimated_casualties=_estimate_casualties(area, release.population_density_per_km2, 0.50),
                area_km2=round(area, 4),
                max_downwind_km=round(max_x, 3),
                max_crosswind_km=round(max_hw, 3),
                contour=contour,
            )
            overall_max_x = max(overall_max_x, max_x)
            overall_max_hw = max(overall_max_hw, max_hw)

    # Compute incapacitating / injury contour
    thr_injury = _concentration_threshold(agent, "incapacitating")
    if thr_injury is not None and thr_injury < (thr_lethal or float("inf")):
        contour, max_x, max_hw = _build_contour(
            release, agent, Q_g_s, H_m, thr_injury, "Injury Zone", cls
        )
        if contour is not None:
            contours.append(contour)
            area = _zone_area(max_x, max_hw)
            injury_zone = CasualtyZone(
                label="Injury Zone",
                estimated_casualties=_estimate_casualties(area, release.population_density_per_km2, 0.30),
                area_km2=round(area, 4),
                max_downwind_km=round(max_x, 3),
                max_crosswind_km=round(max_hw, 3),
                contour=contour,
            )
            overall_max_x = max(overall_max_x, max_x)
            overall_max_hw = max(overall_max_hw, max_hw)

    # Compute IDLH contour
    thr_idlh = _concentration_threshold(agent, "idlh")
    if thr_idlh is not None and thr_idlh < (thr_injury or float("inf")):
        contour, max_x, max_hw = _build_contour(
            release, agent, Q_g_s, H_m, thr_idlh, "IDLH Zone", cls
        )
        if contour is not None:
            contours.append(contour)
            area = _zone_area(max_x, max_hw)
            idlh_zone = CasualtyZone(
                label="IDLH Zone",
                estimated_casualties=_estimate_casualties(area, release.population_density_per_km2, 0.10),
                area_km2=round(area, 4),
                max_downwind_km=round(max_x, 3),
                max_crosswind_km=round(max_hw, 3),
                contour=contour,
            )
            overall_max_x = max(overall_max_x, max_x)
            overall_max_hw = max(overall_max_hw, max_hw)

    # Fallback: if no thresholds defined (e.g. bio with only particle dose), create
    # a rough ALOHA-style threat zone based on source strength
    if not contours:
        # Heuristic: use 1% of centre-line peak concentration as threshold
        peak = _ground_concentration(Q_g_s, 100.0, 0.0, H_m,
                                      release.met.wind_speed_ms, cls,
                                      release.met.mixing_height_m)
        if peak > 0.0:
            threshold_fallback = peak * 0.01
            contour, max_x, max_hw = _build_contour(
                release, agent, Q_g_s, H_m, threshold_fallback, "Hazard Zone", cls
            )
            if contour is not None:
                contours.append(contour)
                area = _zone_area(max_x, max_hw)
                injury_zone = CasualtyZone(
                    label="Hazard Zone",
                    estimated_casualties=_estimate_casualties(area, release.population_density_per_km2, 0.20),
                    area_km2=round(area, 4),
                    max_downwind_km=round(max_x, 3),
                    max_crosswind_km=round(max_hw, 3),
                    contour=contour,
                )
                overall_max_x = max_x
                overall_max_hw = max_hw

    total_casualties = (
        (lethal_zone.estimated_casualties if lethal_zone else 0)
        + (injury_zone.estimated_casualties if injury_zone else 0)
        + (idlh_zone.estimated_casualties if idlh_zone else 0)
    )
    # Deduplicate: lethal zone is subset of injury zone — take outermost
    if lethal_zone and injury_zone:
        total_casualties = max(
            injury_zone.estimated_casualties,
            lethal_zone.estimated_casualties,
        )
    if idlh_zone:
        total_casualties = max(total_casualties, idlh_zone.estimated_casualties)

    plume_area = _zone_area(overall_max_x, overall_max_hw)

    # Build summary narrative
    summary = (
        f"{agent.name} release of {release.quantity_kg:.1f} kg over "
        f"{release.duration_min:.0f} min. "
        f"Wind {release.met.wind_direction_deg:.0f}° at "
        f"{release.met.wind_speed_ms:.1f} m/s "
        f"(Stability Class {cls.value}). "
        f"Max hazard extent: {overall_max_x:.1f} km downwind, "
        f"{overall_max_hw:.1f} km crosswind. "
        f"Estimated affected population: {total_casualties:,}."
    )

    return DispersionSimulation(
        id=uuid4(),
        release_id=release.id,
        simulated_at=datetime.now(timezone.utc),
        max_downwind_km=round(overall_max_x, 3),
        max_crosswind_km=round(overall_max_hw, 3),
        plume_area_km2=round(plume_area, 4),
        contours=contours,
        lethal_zone=lethal_zone,
        injury_zone=injury_zone,
        idlh_zone=idlh_zone,
        total_estimated_casualties=total_casualties,
        wind_direction_deg=release.met.wind_direction_deg,
        wind_speed_ms=release.met.wind_speed_ms,
        stability_class=cls.value,
        summary=summary,
        protective_actions=agent.protective_action,
        metadata={
            "emission_rate_g_s": round(Q_g_s, 6),
            "effective_height_m": H_m,
            "mixing_height_m": release.met.mixing_height_m,
            "temperature_c": release.met.temperature_c,
            "rh_pct": release.met.relative_humidity_pct,
        },
    )
