from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import get_current_user, require_permission
from app.data.agents import AGENT_CATALOG, AGENT_MAP
from app.models import CBRNAgent, CBRNCategory

router = APIRouter(tags=["agents"])


@router.get("/cbrn/agents", response_model=list[CBRNAgent])
async def list_agents(
    category: CBRNCategory | None = Query(default=None, description="Filter by CBRN category"),
    q: str | None = Query(default=None, description="Full-text search on name/description"),
    user: dict = Depends(get_current_user),
):
    """List CBRN agent catalog with optional filters."""
    require_permission(user, "scenario:read")
    results = AGENT_CATALOG
    if category is not None:
        results = [a for a in results if a.category == category]
    if q:
        ql = q.lower()
        results = [
            a for a in results
            if ql in a.name.lower() or ql in a.description.lower() or ql in a.sub_category.lower()
        ]
    return results


@router.get("/cbrn/agents/{agent_id}", response_model=CBRNAgent)
async def get_agent(
    agent_id: str,
    user: dict = Depends(get_current_user),
):
    """Get a single CBRN agent by ID."""
    require_permission(user, "scenario:read")
    agent = AGENT_MAP.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return agent
