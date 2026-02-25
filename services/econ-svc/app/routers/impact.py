from __future__ import annotations

"""Economic indicators and impact assessment endpoints."""

import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth import (
    classification_allowed_levels,
    enforce_classification_ceiling,
    get_current_user,
    get_user_classification,
    require_permission,
)
from app.engine.impact import calculate_economic_impact
from app.models import (
    ClassificationLevel,
    CreateEconomicIndicatorRequest,
    EconomicImpactAssessment,
    EconomicIndicator,
    ImpactSeverity,
    RunImpactAssessmentRequest,
)

router = APIRouter(tags=["impact"])


# ---------------------------------------------------------------------------
# Economic Indicators
# ---------------------------------------------------------------------------

@router.get("/economic-indicators", response_model=list[EconomicIndicator])
async def list_indicators(
    request: Request,
    country_code: str | None = None,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db

    user_cls = get_user_classification(user)
    allowed = classification_allowed_levels(user_cls)
    cls_placeholders = ", ".join(f"${j + 1}" for j in range(len(allowed)))
    params: list = list(allowed)
    i = len(allowed) + 1

    conditions = [f"classification IN ({cls_placeholders})"]
    if country_code:
        conditions.append(f"country_code = ${i}")
        params.append(country_code)
        i += 1

    query = (
        f"SELECT * FROM econ_indicators "
        f"WHERE {' AND '.join(conditions)} "
        f"ORDER BY country_code, indicator_name"
    )
    rows = await db.fetch(query, *params)
    return [_row_to_indicator(r) for r in rows]


@router.post("/economic-indicators", response_model=EconomicIndicator, status_code=status.HTTP_201_CREATED)
async def create_indicator(
    request: Request,
    body: CreateEconomicIndicatorRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    enforce_classification_ceiling(user, body.classification.value)
    db = request.app.state.db

    row = await db.fetchrow(
        """
        INSERT INTO econ_indicators (
            country_code, indicator_name, value, unit, year, source, classification
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
        """,
        body.country_code,
        body.indicator_name,
        body.value,
        body.unit,
        body.year,
        body.source,
        body.classification.value,
    )
    return _row_to_indicator(row)


# ---------------------------------------------------------------------------
# Impact Assessment
# ---------------------------------------------------------------------------

@router.post("/impact/assess", response_model=EconomicImpactAssessment, status_code=status.HTTP_201_CREATED)
async def run_impact_assessment(
    request: Request,
    body: RunImpactAssessmentRequest,
    user: dict = Depends(get_current_user),
):
    """Run deterministic economic impact assessment for a target country."""
    require_permission(user, "scenario:write")
    enforce_classification_ceiling(user, body.classification.value)
    db = request.app.state.db

    # Fetch the requested sanctions
    sanctions_data: list[dict] = []
    if body.sanction_ids:
        id_strs = [str(sid) for sid in body.sanction_ids]
        placeholders = ", ".join(f"${j + 1}::uuid" for j in range(len(id_strs)))
        rows = await db.fetch(
            f"SELECT sanction_type, status FROM econ_sanction_targets WHERE id IN ({placeholders})",
            *id_strs,
        )
        sanctions_data = [dict(r) for r in rows]

    # Fetch economic indicators for the target country
    indicator_rows = await db.fetch(
        "SELECT country_code, indicator_name, value FROM econ_indicators WHERE country_code = $1",
        body.target_country,
    )
    indicators_data = [dict(r) for r in indicator_rows]

    result = calculate_economic_impact(body.target_country, sanctions_data, indicators_data)

    now = datetime.now(tz=timezone.utc)
    row = await db.fetchrow(
        """
        INSERT INTO econ_impact_assessments (
            scenario_id, target_country, gdp_impact_pct, inflation_rate_change,
            unemployment_change, currency_devaluation_pct, trade_volume_reduction_pct,
            affected_sectors, severity, timeline_months, confidence_score,
            notes, classification
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9, $10, $11, $12, $13)
        RETURNING *
        """,
        str(body.scenario_id) if body.scenario_id else None,
        body.target_country,
        result["gdp_impact_pct"],
        result["inflation_rate_change"],
        result["unemployment_change"],
        result["currency_devaluation_pct"],
        result["trade_volume_reduction_pct"],
        json.dumps(result["affected_sectors"]),
        result["severity"],
        result["timeline_months"],
        result["confidence_score"],
        None,
        body.classification.value,
    )
    return _row_to_assessment(row)


@router.get("/impact/assessments", response_model=list[EconomicImpactAssessment])
async def list_assessments(
    request: Request,
    target_country: str | None = None,
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db

    user_cls = get_user_classification(user)
    allowed = classification_allowed_levels(user_cls)
    cls_placeholders = ", ".join(f"${j + 1}" for j in range(len(allowed)))
    params: list = list(allowed)
    i = len(allowed) + 1

    conditions = [f"classification IN ({cls_placeholders})"]
    if target_country:
        conditions.append(f"target_country = ${i}")
        params.append(target_country)
        i += 1

    params.extend([limit, offset])
    query = (
        f"SELECT * FROM econ_impact_assessments "
        f"WHERE {' AND '.join(conditions)} "
        f"ORDER BY created_at DESC LIMIT ${i} OFFSET ${i + 1}"
    )
    rows = await db.fetch(query, *params)
    return [_row_to_assessment(r) for r in rows]


@router.get("/impact/assessments/{assessment_id}", response_model=EconomicImpactAssessment)
async def get_assessment(
    assessment_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow(
        "SELECT * FROM econ_impact_assessments WHERE id = $1::uuid", assessment_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Assessment not found")
    assessment = _row_to_assessment(row)
    enforce_classification_ceiling(user, assessment.classification.value)
    return assessment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_indicator(row) -> EconomicIndicator:
    return EconomicIndicator(
        id=row["id"],
        country_code=row["country_code"],
        indicator_name=row["indicator_name"],
        value=float(row["value"]),
        unit=row["unit"],
        year=row["year"],
        source=row["source"],
        classification=ClassificationLevel(row["classification"]),
        created_at=row["created_at"],
    )


def _row_to_assessment(row) -> EconomicImpactAssessment:
    sectors = row["affected_sectors"]
    if isinstance(sectors, str):
        sectors = json.loads(sectors)
    elif sectors is None:
        sectors = []

    return EconomicImpactAssessment(
        id=row["id"],
        scenario_id=row["scenario_id"],
        target_country=row["target_country"],
        gdp_impact_pct=float(row["gdp_impact_pct"]),
        inflation_rate_change=float(row["inflation_rate_change"]),
        unemployment_change=float(row["unemployment_change"]),
        currency_devaluation_pct=float(row["currency_devaluation_pct"]),
        trade_volume_reduction_pct=float(row["trade_volume_reduction_pct"]),
        affected_sectors=sectors,
        severity=ImpactSeverity(row["severity"]),
        timeline_months=row["timeline_months"],
        confidence_score=float(row["confidence_score"]),
        notes=row["notes"],
        classification=ClassificationLevel(row["classification"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
