from __future__ import annotations

"""Trade route CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth import (
    classification_allowed_levels,
    enforce_classification_ceiling,
    get_current_user,
    get_user_classification,
    require_permission,
)
from app.models import (
    ClassificationLevel,
    CreateTradeRouteRequest,
    TradeDependency,
    TradeRoute,
    UpdateTradeRouteRequest,
)

router = APIRouter(tags=["trade"])


@router.get("/trade-routes", response_model=list[TradeRoute])
async def list_trade_routes(
    request: Request,
    limit: int = 100,
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
    params.extend([limit, offset])
    query = (
        f"SELECT * FROM econ_trade_routes "
        f"WHERE classification IN ({cls_placeholders}) "
        f"ORDER BY created_at DESC LIMIT ${i} OFFSET ${i + 1}"
    )
    rows = await db.fetch(query, *params)
    return [_row_to_trade_route(r) for r in rows]


@router.post("/trade-routes", response_model=TradeRoute, status_code=status.HTTP_201_CREATED)
async def create_trade_route(
    request: Request,
    body: CreateTradeRouteRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    enforce_classification_ceiling(user, body.classification.value)
    db = request.app.state.db

    row = await db.fetchrow(
        """
        INSERT INTO econ_trade_routes (
            origin_country, destination_country, commodity,
            annual_value_usd, dependency_level, is_disrupted,
            disruption_cause, classification
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING *
        """,
        body.origin_country,
        body.destination_country,
        body.commodity,
        body.annual_value_usd,
        body.dependency_level.value,
        body.is_disrupted,
        body.disruption_cause,
        body.classification.value,
    )
    return _row_to_trade_route(row)


@router.get("/trade-routes/{route_id}", response_model=TradeRoute)
async def get_trade_route(
    route_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow(
        "SELECT * FROM econ_trade_routes WHERE id = $1::uuid", route_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Trade route not found")
    route = _row_to_trade_route(row)
    enforce_classification_ceiling(user, route.classification.value)
    return route


@router.put("/trade-routes/{route_id}", response_model=TradeRoute)
async def update_trade_route(
    route_id: str,
    request: Request,
    body: UpdateTradeRouteRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db

    existing = await db.fetchrow(
        "SELECT classification FROM econ_trade_routes WHERE id = $1::uuid", route_id
    )
    if existing:
        enforce_classification_ceiling(user, existing["classification"])
    if body.classification is not None:
        enforce_classification_ceiling(user, body.classification.value)

    updates = []
    params: list = []
    i = 1

    if body.commodity is not None:
        updates.append(f"commodity = ${i}")
        params.append(body.commodity)
        i += 1
    if body.annual_value_usd is not None:
        updates.append(f"annual_value_usd = ${i}")
        params.append(body.annual_value_usd)
        i += 1
    if body.dependency_level is not None:
        updates.append(f"dependency_level = ${i}")
        params.append(body.dependency_level.value)
        i += 1
    if body.is_disrupted is not None:
        updates.append(f"is_disrupted = ${i}")
        params.append(body.is_disrupted)
        i += 1
    if body.disruption_cause is not None:
        updates.append(f"disruption_cause = ${i}")
        params.append(body.disruption_cause)
        i += 1
    if body.classification is not None:
        updates.append(f"classification = ${i}")
        params.append(body.classification.value)
        i += 1

    if not updates:
        row = await db.fetchrow(
            "SELECT * FROM econ_trade_routes WHERE id = $1::uuid", route_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Trade route not found")
        return _row_to_trade_route(row)

    updates.append("updated_at = NOW()")
    params.append(route_id)
    query = (
        f"UPDATE econ_trade_routes SET {', '.join(updates)} "
        f"WHERE id = ${i}::uuid RETURNING *"
    )
    row = await db.fetchrow(query, *params)
    if not row:
        raise HTTPException(status_code=404, detail="Trade route not found")
    return _row_to_trade_route(row)


@router.delete("/trade-routes/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trade_route(
    route_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db
    result = await db.execute(
        "DELETE FROM econ_trade_routes WHERE id = $1::uuid", route_id
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Trade route not found")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_trade_route(row) -> TradeRoute:
    return TradeRoute(
        id=row["id"],
        origin_country=row["origin_country"],
        destination_country=row["destination_country"],
        commodity=row["commodity"],
        annual_value_usd=row["annual_value_usd"],
        dependency_level=TradeDependency(row["dependency_level"]),
        is_disrupted=row["is_disrupted"],
        disruption_cause=row["disruption_cause"],
        classification=ClassificationLevel(row["classification"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
