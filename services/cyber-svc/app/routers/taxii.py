from __future__ import annotations

"""STIX 2.1 / TAXII 2.1 threat intelligence feed consumer."""

import json
import time
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth import get_current_user, require_permission
from app.models import (
    CreateSTIXIndicatorRequest,
    STIXIndicator,
    TAXIIIngestRequest,
    TAXIIIngestResult,
)

router = APIRouter(tags=["taxii"])

# ---------------------------------------------------------------------------
# STIX Indicator CRUD
# ---------------------------------------------------------------------------

@router.get("/cyber/stix/indicators", response_model=list[STIXIndicator])
async def list_stix_indicators(
    request: Request,
    scenario_id: str | None = None,
    taxii_server: str | None = None,
    indicator_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(get_current_user),
):
    """List STIX indicators, optionally filtered by scenario, server, or type."""
    require_permission(user, "scenario:read")
    db = request.app.state.db

    conditions = ["1=1"]
    params: list = []
    i = 1
    if scenario_id:
        conditions.append(f"scenario_id = ${i}::uuid")
        params.append(scenario_id)
        i += 1
    if taxii_server:
        conditions.append(f"taxii_server = ${i}")
        params.append(taxii_server)
        i += 1
    if indicator_type:
        conditions.append(f"${i} = ANY(indicator_types)")
        params.append(indicator_type)
        i += 1
    conditions.append(f"LIMIT ${i} OFFSET ${i+1}")
    params.extend([limit, offset])

    rows = await db.fetch(
        f"SELECT * FROM stix_indicators WHERE {' AND '.join(conditions[:-1])} {conditions[-1]}",
        *params,
    )
    return [_row_to_indicator(r) for r in rows]


@router.post("/cyber/stix/indicators", response_model=STIXIndicator, status_code=status.HTTP_201_CREATED)
async def create_stix_indicator(
    request: Request,
    body: CreateSTIXIndicatorRequest,
    user: dict = Depends(get_current_user),
):
    """Manually create a STIX indicator."""
    require_permission(user, "scenario:write")
    db = request.app.state.db

    now = datetime.now(tz=timezone.utc)
    stix_id = body.stix_id or f"indicator--{uuid4()}"

    row = await db.fetchrow(
        """
        INSERT INTO stix_indicators (
            stix_id, name, description, pattern, pattern_type,
            indicator_types, kill_chain_phases, confidence, labels,
            valid_from, valid_until, created, modified,
            external_references, taxii_collection, taxii_server,
            classification, scenario_id
        ) VALUES (
            $1, $2, $3, $4, $5,
            $6::text[], $7::jsonb, $8, $9::text[],
            $10, $11, $12, $13,
            $14::jsonb, $15, $16,
            $17::classification_level, $18
        )
        ON CONFLICT (stix_id) DO UPDATE SET
            modified = EXCLUDED.modified,
            confidence = EXCLUDED.confidence
        RETURNING *
        """,
        stix_id,
        body.name,
        body.description,
        body.pattern,
        body.pattern_type.value,
        list(body.indicator_types),
        json.dumps([kc.model_dump() for kc in body.kill_chain_phases]),
        body.confidence,
        list(body.labels),
        body.valid_from,
        body.valid_until,
        now,
        now,
        json.dumps([er.model_dump(exclude_none=True) for er in body.external_references]),
        body.taxii_collection,
        body.taxii_server,
        body.classification,
        str(body.scenario_id) if body.scenario_id else None,
    )
    return _row_to_indicator(row)


@router.get("/cyber/stix/indicators/{indicator_id}", response_model=STIXIndicator)
async def get_stix_indicator(
    indicator_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db
    row = await db.fetchrow("SELECT * FROM stix_indicators WHERE id = $1::uuid", indicator_id)
    if not row:
        raise HTTPException(status_code=404, detail="STIX indicator not found")
    return _row_to_indicator(row)


@router.delete("/cyber/stix/indicators/{indicator_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stix_indicator(
    indicator_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db
    result = await db.execute("DELETE FROM stix_indicators WHERE id = $1::uuid", indicator_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="STIX indicator not found")


# ---------------------------------------------------------------------------
# TAXII Ingest
# ---------------------------------------------------------------------------

@router.post("/cyber/taxii/ingest", response_model=TAXIIIngestResult)
async def taxii_ingest(
    request: Request,
    body: TAXIIIngestRequest,
    user: dict = Depends(get_current_user),
):
    """
    Poll a TAXII 2.1 server collection for STIX objects and ingest them.

    Attempts a live TAXII connection; falls back to synthetic demo data if the
    server is unreachable (air-gap / development mode).
    """
    require_permission(user, "scenario:write")
    db = request.app.state.db

    t0 = time.perf_counter()
    items_fetched = 0
    items_saved = 0
    errors: list[str] = []

    try:
        import httpx

        headers = {"Accept": "application/taxii+json;version=2.1"}
        if body.api_key:
            headers["Authorization"] = f"Bearer {body.api_key}"

        url = f"{body.server_url.rstrip('/')}/collections/{body.collection_id}/objects/"
        params = {"match[type]": "indicator", "limit": str(body.max_items)}

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            envelope = resp.json()
            objects = envelope.get("objects", [])

    except Exception as exc:
        # Fall back to synthetic STIX bundle
        errors.append(f"TAXII connection failed: {exc}. Using synthetic demo data.")
        objects = _synthetic_stix_bundle()

    for obj in objects[:body.max_items]:
        if obj.get("type") != "indicator":
            continue
        items_fetched += 1
        if body.dry_run:
            items_saved += 1
            continue

        now = datetime.now(tz=timezone.utc)
        stix_id = obj.get("id", f"indicator--{uuid4()}")

        try:
            await db.execute(
                """
                INSERT INTO stix_indicators (
                    stix_id, name, description, pattern, pattern_type,
                    indicator_types, kill_chain_phases, confidence, labels,
                    valid_from, valid_until, created, modified,
                    created_by_ref, external_references,
                    taxii_collection, taxii_server, classification
                ) VALUES (
                    $1, $2, $3, $4, $5,
                    $6::text[], $7::jsonb, $8, $9::text[],
                    $10, $11, $12, $13,
                    $14, $15::jsonb,
                    $16, $17, $18::classification_level
                )
                ON CONFLICT (stix_id) DO UPDATE SET
                    modified = EXCLUDED.modified,
                    confidence = EXCLUDED.confidence,
                    pattern = EXCLUDED.pattern
                """,
                stix_id,
                obj.get("name", stix_id),
                obj.get("description"),
                obj.get("pattern", ""),
                obj.get("pattern_type", "stix"),
                obj.get("indicator_types", []),
                json.dumps(obj.get("kill_chain_phases", [])),
                obj.get("confidence", 50),
                obj.get("labels", []),
                _parse_dt(obj.get("valid_from")) or now,
                _parse_dt(obj.get("valid_until")),
                _parse_dt(obj.get("created")) or now,
                _parse_dt(obj.get("modified")) or now,
                obj.get("created_by_ref"),
                json.dumps(obj.get("external_references", [])),
                body.collection_id,
                body.server_url,
                "UNCLASS",
            )
            items_saved += 1
        except Exception as exc:
            errors.append(f"DB insert error for {stix_id}: {exc}")

    return TAXIIIngestResult(
        server_url=body.server_url,
        collection_id=body.collection_id,
        items_fetched=items_fetched,
        items_saved=items_saved,
        errors=errors,
        dry_run=body.dry_run,
        duration_seconds=round(time.perf_counter() - t0, 3),
    )


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _row_to_indicator(row) -> STIXIndicator:
    from app.models import KillChainPhase, ExternalReference, PatternType

    kc_phases = [KillChainPhase(**kc) for kc in (row["kill_chain_phases"] or [])]
    ext_refs = [ExternalReference(**er) for er in (row["external_references"] or [])]

    return STIXIndicator(
        id=row["id"],
        stix_id=row["stix_id"],
        stix_type=row["stix_type"],
        spec_version=row["spec_version"],
        name=row["name"],
        description=row["description"],
        pattern=row["pattern"],
        pattern_type=PatternType(row["pattern_type"]),
        indicator_types=list(row["indicator_types"] or []),
        kill_chain_phases=kc_phases,
        confidence=row["confidence"],
        labels=list(row["labels"] or []),
        valid_from=row["valid_from"],
        valid_until=row["valid_until"],
        created=row["created"],
        modified=row["modified"],
        created_by_ref=row["created_by_ref"],
        external_references=ext_refs,
        taxii_collection=row["taxii_collection"],
        taxii_server=row["taxii_server"],
        classification=row["classification"],
        scenario_id=row["scenario_id"],
        ingested_at=row["ingested_at"],
    )


def _synthetic_stix_bundle() -> list[dict]:
    """Return a realistic synthetic STIX 2.1 indicator bundle for demo/air-gap use."""
    now = datetime.now(tz=timezone.utc).isoformat()
    return [
        {
            "type": "indicator",
            "spec_version": "2.1",
            "id": f"indicator--{uuid4()}",
            "name": "Cobalt Strike Beacon C2 — APT29",
            "description": (
                "Network indicator for Cobalt Strike Beacon command-and-control traffic "
                "attributed to APT29 (Cozy Bear). HTTPS POST to /jquery-3.3.1.min.js path "
                "with characteristic jitter and sleep timers."
            ),
            "pattern": "[network-traffic:dst_ref.type = 'ipv4-addr' AND network-traffic:dst_ref.value = '185.220.101.45']",
            "pattern_type": "stix",
            "indicator_types": ["malicious-activity", "compromised"],
            "kill_chain_phases": [
                {"kill_chain_name": "mitre-attack", "phase_name": "command-and-control"}
            ],
            "confidence": 85,
            "labels": ["apt29", "cobalt-strike", "c2"],
            "valid_from": now,
            "created": now,
            "modified": now,
            "external_references": [
                {
                    "source_name": "MITRE ATT&CK",
                    "url": "https://attack.mitre.org/techniques/T1071/001/",
                    "external_id": "T1071.001",
                }
            ],
        },
        {
            "type": "indicator",
            "spec_version": "2.1",
            "id": f"indicator--{uuid4()}",
            "name": "SUNBURST Malware SHA-256",
            "description": (
                "SHA-256 hash of SUNBURST backdoor DLL distributed via SolarWinds Orion "
                "platform update 2020.2.1 HF1. Attributed to APT29 / UNC2452."
            ),
            "pattern": "[file:hashes.'SHA-256' = '019085a76ba7126fff22770d71bd901c325fc68ac55aa743327984e89f4b0134']",
            "pattern_type": "stix",
            "indicator_types": ["malicious-activity"],
            "kill_chain_phases": [
                {"kill_chain_name": "mitre-attack", "phase_name": "initial-access"}
            ],
            "confidence": 99,
            "labels": ["apt29", "sunburst", "supply-chain"],
            "valid_from": now,
            "created": now,
            "modified": now,
        },
        {
            "type": "indicator",
            "spec_version": "2.1",
            "id": f"indicator--{uuid4()}",
            "name": "Industroyer2 ICS Malware Domain",
            "description": (
                "Domain used for command-and-control by Industroyer2 ICS-targeting malware. "
                "Attributed to Sandworm (APT44). Targets IEC 104 protocol in Ukrainian power grid."
            ),
            "pattern": "[domain-name:value = 'update.microsoft-update[.]info']",
            "pattern_type": "stix",
            "indicator_types": ["malicious-activity", "anomalous-activity"],
            "kill_chain_phases": [
                {"kill_chain_name": "mitre-attack", "phase_name": "impact"}
            ],
            "confidence": 92,
            "labels": ["sandworm", "ics", "industroyer2", "ukraine"],
            "valid_from": now,
            "created": now,
            "modified": now,
        },
        {
            "type": "indicator",
            "spec_version": "2.1",
            "id": f"indicator--{uuid4()}",
            "name": "Lazarus Group Phishing URL — Financial Sector",
            "description": (
                "URL used in SWIFT-targeting spear-phishing campaign by Lazarus Group (APT38). "
                "Hosts a fake banking portal to harvest credentials."
            ),
            "pattern": "[url:value = 'https://swift-secure-portal[.]com/login']",
            "pattern_type": "stix",
            "indicator_types": ["malicious-activity"],
            "kill_chain_phases": [
                {"kill_chain_name": "mitre-attack", "phase_name": "initial-access"}
            ],
            "confidence": 78,
            "labels": ["lazarus", "apt38", "swift", "phishing"],
            "valid_from": now,
            "created": now,
            "modified": now,
        },
        {
            "type": "indicator",
            "spec_version": "2.1",
            "id": f"indicator--{uuid4()}",
            "name": "BlackEnergy PowerShell Dropper — YARA Rule",
            "description": (
                "YARA rule detecting BlackEnergy 3 PowerShell dropper used against Ukrainian "
                "critical infrastructure. Detects obfuscated Base64-encoded stage-1 loader."
            ),
            "pattern": (
                "rule BlackEnergy3_PS_Dropper { strings: $a = \"[System.Text.Encoding]::Unicode.GetString\" "
                "$b = \"FromBase64String\" $c = \"Invoke-Expression\" condition: all of them }"
            ),
            "pattern_type": "yara",
            "indicator_types": ["malicious-activity"],
            "kill_chain_phases": [
                {"kill_chain_name": "mitre-attack", "phase_name": "execution"}
            ],
            "confidence": 88,
            "labels": ["blackenergy", "sandworm", "ukraine", "ics"],
            "valid_from": now,
            "created": now,
            "modified": now,
        },
    ]
