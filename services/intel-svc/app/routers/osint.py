from __future__ import annotations

"""OSINT ingestion pipeline endpoints."""

from fastapi import APIRouter, Depends, Request

from app.auth import get_current_user, require_permission
from app.engine.osint_adapters import get_adapter, list_adapters, run_ingestion
from app.models import IngestRequest, IngestResult, OSINTSource, OSINTSourceStatus

router = APIRouter(tags=["osint"])


@router.get("/intel/osint/sources", response_model=list[OSINTSource])
async def list_osint_sources(
    request: Request,
    user: dict = Depends(get_current_user),
):
    """List all configured OSINT source adapters and their current status."""
    require_permission(user, "scenario:read")
    db = request.app.state.db

    sources = []
    for adapter in list_adapters():
        info = adapter.get_source_info()

        # Look up last ingestion record
        row = await db.fetchrow(
            """
            SELECT MAX(ingested_at) AS last_run, COUNT(*) AS total_items
            FROM intel_items
            WHERE source_type = 'OSINT'
            """,
        )
        if row:
            info.last_ingested_at = row["last_run"]
            info.items_ingested = int(row["total_items"])

        sources.append(info)

    return sources


@router.post("/intel/osint/ingest", response_model=IngestResult)
async def trigger_ingestion(
    request: Request,
    body: IngestRequest,
    user: dict = Depends(get_current_user),
):
    """
    Trigger an OSINT ingestion run for the specified source adapter.

    Fetches recent events from ACLED, UCDP, or RSS feeds and inserts them
    into the intel_items table with auto entity extraction.

    Set *dry_run=true* to preview what would be fetched without saving.
    """
    require_permission(user, "scenario:write")
    db = request.app.state.db

    adapter = get_adapter(body.source_id)
    if adapter is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail=f"OSINT source '{body.source_id}' not found. "
                   "Available sources: acled, ucdp, rss",
        )

    return await run_ingestion(body, db, auto_extract=True)
