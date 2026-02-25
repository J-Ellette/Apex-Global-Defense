from __future__ import annotations

"""Report generation and management endpoints."""

import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth import get_current_user, require_permission
from app.engine.templates import generate_conops, generate_intsum, generate_sitrep
from app.models import (
    ApproveReportRequest,
    GenerateReportRequest,
    Report,
    ReportStatus,
    ReportType,
    UpdateReportRequest,
)

router = APIRouter(tags=["reports"])


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

@router.post("/reports/generate", response_model=Report, status_code=status.HTTP_201_CREATED)
async def generate_report(
    request: Request,
    body: GenerateReportRequest,
    user: dict = Depends(get_current_user),
):
    """
    Generate a structured report (SITREP, INTSUM, or CONOPS) from simulation
    and intelligence data.  The report is saved as a DRAFT and returned.
    """
    require_permission(user, "scenario:read")
    db = request.app.state.db

    scenario_name = "AGD SCENARIO"

    # Try to fetch scenario name
    if body.scenario_id:
        try:
            row = await db.fetchrow(
                "SELECT name FROM scenarios WHERE id = $1",
                str(body.scenario_id),
            )
            if row:
                scenario_name = row["name"]
        except Exception:
            pass

    # Fetch run events if run_id is provided (from simulation_runs / sim_events)
    run_events: list[dict] = []
    logistics: dict = {}
    if body.run_id:
        try:
            event_rows = await db.fetch(
                "SELECT event_type, turn, payload FROM sim_events WHERE run_id = $1 ORDER BY turn",
                str(body.run_id),
            )
            run_events = [
                {
                    "event_type": r["event_type"],
                    "turn": r["turn"],
                    "payload": json.loads(r["payload"]) if r["payload"] else {},
                }
                for r in event_rows
            ]
        except Exception:
            pass

    # Dispatch to the appropriate template generator
    if body.report_type == ReportType.SITREP:
        result = generate_sitrep(
            scenario_name=scenario_name,
            run_events=run_events,
            logistics=logistics,
            context=body.context,
        )
        title = body.title or f"SITREP — {scenario_name} — {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H%MZ')}"

    elif body.report_type == ReportType.INTSUM:
        result = generate_intsum(
            scenario_name=scenario_name,
            context=body.context,
        )
        title = body.title or f"INTSUM — {scenario_name} — {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H%MZ')}"

    else:  # CONOPS
        result = generate_conops(
            scenario_name=scenario_name,
            context=body.context,
        )
        title = body.title or f"CONOPS — {scenario_name} — {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H%MZ')}"

    author_id: str | None = user.get("uid")
    now = datetime.now(tz=timezone.utc)

    row = await db.fetchrow(
        """
        INSERT INTO reports (
            scenario_id, run_id, report_type, title, classification,
            author_id, status, content, summary
        ) VALUES (
            $1, $2, $3, $4, $5::classification_level,
            $6, $7, $8::jsonb, $9
        )
        RETURNING *
        """,
        str(body.scenario_id) if body.scenario_id else None,
        str(body.run_id) if body.run_id else None,
        body.report_type.value,
        title,
        body.classification.value,
        author_id,
        ReportStatus.DRAFT.value,
        json.dumps(result["content"]),
        result["summary"],
    )
    return _row_to_report(row)


# ---------------------------------------------------------------------------
# Report CRUD
# ---------------------------------------------------------------------------

@router.get("/reports", response_model=list[Report])
async def list_reports(
    request: Request,
    scenario_id: str | None = None,
    report_type: ReportType | None = None,
    status: ReportStatus | None = None,
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(get_current_user),
):
    """List reports with optional filters."""
    require_permission(user, "scenario:read")
    db = request.app.state.db

    conditions = ["1=1"]
    params: list = []
    i = 1

    if scenario_id:
        conditions.append(f"scenario_id = ${i}::uuid")
        params.append(scenario_id)
        i += 1
    if report_type:
        conditions.append(f"report_type = ${i}")
        params.append(report_type.value)
        i += 1
    if status:
        conditions.append(f"status = ${i}")
        params.append(status.value)
        i += 1

    params.extend([limit, offset])
    query = (
        f"SELECT * FROM reports WHERE {' AND '.join(conditions)} "
        f"ORDER BY created_at DESC LIMIT ${i} OFFSET ${i+1}"
    )
    rows = await db.fetch(query, *params)
    return [_row_to_report(r) for r in rows]


@router.get("/reports/{report_id}", response_model=Report)
async def get_report(
    report_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow("SELECT * FROM reports WHERE id = $1::uuid", report_id)
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    return _row_to_report(row)


@router.put("/reports/{report_id}", response_model=Report)
async def update_report(
    report_id: str,
    request: Request,
    body: UpdateReportRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db

    updates = []
    params: list = []
    i = 1

    if body.title is not None:
        updates.append(f"title = ${i}")
        params.append(body.title)
        i += 1
    if body.status is not None:
        updates.append(f"status = ${i}")
        params.append(body.status.value)
        i += 1
    if body.classification is not None:
        updates.append(f"classification = ${i}::classification_level")
        params.append(body.classification.value)
        i += 1
    if body.content is not None:
        updates.append(f"content = ${i}::jsonb")
        params.append(json.dumps(body.content))
        i += 1
    if body.summary is not None:
        updates.append(f"summary = ${i}")
        params.append(body.summary)
        i += 1

    if not updates:
        row = await db.fetchrow("SELECT * FROM reports WHERE id = $1::uuid", report_id)
        if not row:
            raise HTTPException(status_code=404, detail="Report not found")
        return _row_to_report(row)

    updates.append(f"updated_at = NOW()")
    params.append(report_id)
    query = f"UPDATE reports SET {', '.join(updates)} WHERE id = ${i}::uuid RETURNING *"
    row = await db.fetchrow(query, *params)
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    return _row_to_report(row)


@router.post("/reports/{report_id}/approve", response_model=Report)
async def approve_report(
    report_id: str,
    request: Request,
    body: ApproveReportRequest,
    user: dict = Depends(get_current_user),
):
    """Mark a FINAL report as APPROVED."""
    require_permission(user, "scenario:write")
    db = request.app.state.db

    row = await db.fetchrow(
        """
        UPDATE reports
        SET status = 'APPROVED', approved_by = $1, approved_at = NOW(), updated_at = NOW()
        WHERE id = $2::uuid
        RETURNING *
        """,
        body.approved_by,
        report_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    return _row_to_report(row)


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db
    result = await db.execute("DELETE FROM reports WHERE id = $1::uuid", report_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Report not found")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_report(row) -> Report:
    from app.models import ClassificationLevel, ReportStatus, ReportType

    return Report(
        id=row["id"],
        scenario_id=row["scenario_id"],
        run_id=row["run_id"],
        report_type=ReportType(row["report_type"]),
        title=row["title"],
        classification=ClassificationLevel(row["classification"]),
        author_id=row["author_id"],
        status=ReportStatus(row["status"]),
        content=row["content"] if row["content"] else {},
        summary=row["summary"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        approved_by=row["approved_by"],
        approved_at=row["approved_at"],
    )
