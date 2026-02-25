from __future__ import annotations

"""Intel item CRUD + full-text / geo / date search + semantic search (pgvector stub)."""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import (
    classification_allowed_levels,
    enforce_classification_ceiling,
    get_current_user,
    get_user_classification,
    require_permission,
)
from app.engine.extractor import extract_entities
from app.models import (
    ClassificationLevel,
    CreateIntelItemRequest,
    EntityType,
    IntelItem,
    SearchRequest,
    SearchResult,
    SemanticSearchRequest,
    SourceType,
    UpdateIntelItemRequest,
    ExtractedEntity,
)

router = APIRouter(tags=["intel"])


# ---------------------------------------------------------------------------
# Row → model helper
# ---------------------------------------------------------------------------

def _row_to_item(row: dict) -> IntelItem:
    entities_raw = row.get("entities") or []
    if isinstance(entities_raw, str):
        entities_raw = json.loads(entities_raw)

    entities = []
    for e in entities_raw:
        try:
            entities.append(ExtractedEntity(
                type=EntityType(e["type"]) if isinstance(e.get("type"), str) else e["type"],
                text=e["text"],
                confidence=float(e.get("confidence", 0.7)),
            ))
        except Exception:
            pass

    lat: float | None = None
    lon: float | None = None
    if row.get("lat") is not None:
        lat = float(row["lat"])
    if row.get("lon") is not None:
        lon = float(row["lon"])

    return IntelItem(
        id=row["id"],
        source_type=SourceType(row["source_type"]) if row.get("source_type") else SourceType.OSINT,
        source_url=row.get("source_url"),
        title=row.get("title") or "",
        content=row.get("content") or "",
        language=row.get("language") or "eng",
        latitude=lat,
        longitude=lon,
        entities=entities,
        classification=ClassificationLevel(row["classification"]) if row.get("classification") else ClassificationLevel.UNCLASS,
        reliability=row.get("reliability") or "F",
        credibility=row.get("credibility") or "6",
        published_at=row.get("published_at"),
        ingested_at=row["ingested_at"],
        has_embedding=row.get("embedding") is not None,
    )


# ---------------------------------------------------------------------------
# CRUD endpoints
# ---------------------------------------------------------------------------

@router.get("/intel", response_model=list[IntelItem])
async def list_intel_items(
    request: Request,
    source_type: SourceType | None = None,
    classification: ClassificationLevel | None = None,
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(get_current_user),
):
    """List intel items with optional source_type / classification filters."""
    require_permission(user, "scenario:read")
    db = request.app.state.db

    # Application-level classification ceiling: only return records the user is cleared for
    user_cls = get_user_classification(user)
    allowed = classification_allowed_levels(user_cls)

    clauses: list[str] = []
    params: list = []
    p = 1

    # Always restrict to user's clearance ceiling (defense-in-depth alongside DB RLS)
    placeholders = ", ".join(f"${p + i}::classification_level" for i in range(len(allowed)))
    clauses.append(f"classification IN ({placeholders})")
    params.extend(allowed)
    p += len(allowed)

    if source_type:
        clauses.append(f"source_type = ${p}::source_type")
        params.append(source_type.value)
        p += 1
    if classification:
        # Requested filter must be within user's allowed levels
        if classification.value not in allowed:
            return []
        clauses.append(f"classification = ${p}::classification_level")
        params.append(classification.value)
        p += 1

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    params.extend([limit, offset])

    rows = await db.fetch(
        f"""
        SELECT id, source_type, source_url, title, content, language,
               ST_Y(location::geometry) AS lat,
               ST_X(location::geometry) AS lon,
               entities, classification, reliability, credibility,
               published_at, ingested_at,
               embedding IS NOT NULL AS has_emb
        FROM intel_items
        {where}
        ORDER BY ingested_at DESC
        LIMIT ${p} OFFSET ${p + 1}
        """,
        *params,
    )
    return [_row_to_item(dict(r)) for r in rows]


@router.post("/intel", response_model=IntelItem, status_code=201)
async def create_intel_item(
    request: Request,
    body: CreateIntelItemRequest,
    user: dict = Depends(get_current_user),
):
    """Ingest a new intelligence item. Optionally runs entity extraction."""
    require_permission(user, "scenario:write")
    enforce_classification_ceiling(user, body.classification.value)
    db = request.app.state.db

    entities_json: list[dict] = []
    if body.auto_extract:
        extracted = extract_entities(body.content)
        entities_json = [
            {"type": e.type.value, "text": e.text, "confidence": e.confidence}
            for e in extracted
        ]

    location_wkt = None
    if body.latitude is not None and body.longitude is not None:
        location_wkt = f"POINT({body.longitude} {body.latitude})"

    row = await db.fetchrow(
        """
        INSERT INTO intel_items (
            source_type, source_url, title, content, language,
            location, entities, classification, reliability, credibility,
            published_at, ingested_at
        ) VALUES (
            $1::source_type, $2, $3, $4, $5,
            ST_GeomFromText($6, 4326),
            $7::jsonb, $8::classification_level, $9, $10,
            $11, NOW()
        )
        RETURNING id, source_type, source_url, title, content, language,
                  ST_Y(location::geometry) AS lat,
                  ST_X(location::geometry) AS lon,
                  entities, classification, reliability, credibility,
                  published_at, ingested_at
        """,
        body.source_type.value,  # asyncpg will map to source_type enum via text
        body.source_url,
        body.title,
        body.content,
        body.language,
        location_wkt,
        json.dumps(entities_json),
        body.classification.value,
        body.reliability,
        body.credibility,
        body.published_at,
    )
    return _row_to_item(dict(row))


@router.get("/intel/{item_id}", response_model=IntelItem)
async def get_intel_item(
    request: Request,
    item_id: UUID,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:read")
    db = request.app.state.db

    row = await db.fetchrow(
        """
        SELECT id, source_type, source_url, title, content, language,
               ST_Y(location::geometry) AS lat,
               ST_X(location::geometry) AS lon,
               entities, classification, reliability, credibility,
               published_at, ingested_at,
               embedding IS NOT NULL AS has_emb
        FROM intel_items WHERE id = $1
        """,
        item_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Intel item not found")
    item = _row_to_item(dict(row))
    enforce_classification_ceiling(user, item.classification.value)
    return item


@router.put("/intel/{item_id}", response_model=IntelItem)
async def update_intel_item(
    request: Request,
    item_id: UUID,
    body: UpdateIntelItemRequest,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db

    existing = await db.fetchrow("SELECT id, classification FROM intel_items WHERE id = $1", item_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Intel item not found")
    enforce_classification_ceiling(user, existing["classification"])
    if body.classification is not None:
        enforce_classification_ceiling(user, body.classification.value)

    updates: list[str] = []
    params: list = []
    p = 1

    for field, col in [
        ("title", "title"),
        ("content", "content"),
        ("reliability", "reliability"),
        ("credibility", "credibility"),
    ]:
        val = getattr(body, field)
        if val is not None:
            updates.append(f"{col} = ${p}")
            params.append(val)
            p += 1

    if body.classification is not None:
        updates.append(f"classification = ${p}::classification_level")
        params.append(body.classification.value)
        p += 1

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(item_id)
    row = await db.fetchrow(
        f"""
        UPDATE intel_items SET {', '.join(updates)}
        WHERE id = ${p}
        RETURNING id, source_type, source_url, title, content, language,
                  ST_Y(location::geometry) AS lat,
                  ST_X(location::geometry) AS lon,
                  entities, classification, reliability, credibility,
                  published_at, ingested_at
        """,
        *params,
    )
    return _row_to_item(dict(row))


@router.delete("/intel/{item_id}", status_code=204)
async def delete_intel_item(
    request: Request,
    item_id: UUID,
    user: dict = Depends(get_current_user),
):
    require_permission(user, "scenario:write")
    db = request.app.state.db

    result = await db.execute("DELETE FROM intel_items WHERE id = $1", item_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Intel item not found")


# ---------------------------------------------------------------------------
# Search endpoints
# ---------------------------------------------------------------------------

@router.post("/intel/search", response_model=SearchResult)
async def search_intel(
    request: Request,
    body: SearchRequest,
    user: dict = Depends(get_current_user),
):
    """
    Full-text + geo + date filter search across intelligence items.
    Supports free-text query (title + content), source type, classification,
    geographic bounding (lat/lon + radius_km), and date range.
    """
    require_permission(user, "scenario:read")
    db = request.app.state.db

    # Application-level classification ceiling enforcement
    user_cls = get_user_classification(user)
    allowed = classification_allowed_levels(user_cls)

    clauses: list[str] = []
    params: list = []
    p = 1

    # Always restrict to user's clearance ceiling
    cls_placeholders = ", ".join(f"${p + i}::classification_level" for i in range(len(allowed)))
    clauses.append(f"classification IN ({cls_placeholders})")
    params.extend(allowed)
    p += len(allowed)

    if body.q:
        clauses.append(
            f"(to_tsvector('english', title || ' ' || content) @@ plainto_tsquery('english', ${p}))"
        )
        params.append(body.q)
        p += 1

    if body.source_types:
        placeholders = ", ".join(f"${p + i}::source_type" for i in range(len(body.source_types)))
        clauses.append(f"source_type IN ({placeholders})")
        params.extend(st.value for st in body.source_types)
        p += len(body.source_types)

    if body.classification:
        # Only apply if requested classification is within user's allowed levels
        if body.classification.value in allowed:
            clauses.append(f"classification = ${p}::classification_level")
            params.append(body.classification.value)
            p += 1

    if body.lat is not None and body.lon is not None and body.radius_km:
        clauses.append(
            f"ST_DWithin(location::geography, ST_MakePoint(${p}, ${p+1})::geography, ${p+2})"
        )
        params.extend([body.lon, body.lat, body.radius_km * 1000])
        p += 3

    if body.from_date:
        clauses.append(f"ingested_at >= ${p}")
        params.append(body.from_date)
        p += 1

    if body.to_date:
        clauses.append(f"ingested_at <= ${p}")
        params.append(body.to_date)
        p += 1

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

    count_row = await db.fetchrow(
        f"SELECT COUNT(*) AS cnt FROM intel_items {where}", *params
    )
    total = int(count_row["cnt"]) if count_row else 0

    params.extend([body.limit, body.offset])
    rows = await db.fetch(
        f"""
        SELECT id, source_type, source_url, title, content, language,
               ST_Y(location::geometry) AS lat,
               ST_X(location::geometry) AS lon,
               entities, classification, reliability, credibility,
               published_at, ingested_at,
               embedding IS NOT NULL AS has_emb
        FROM intel_items {where}
        ORDER BY ingested_at DESC
        LIMIT ${p} OFFSET ${p + 1}
        """,
        *params,
    )

    return SearchResult(
        items=[_row_to_item(dict(r)) for r in rows],
        total=total,
        limit=body.limit,
        offset=body.offset,
    )


@router.post("/intel/semantic-search", response_model=SearchResult)
async def semantic_search(
    request: Request,
    body: SemanticSearchRequest,
    user: dict = Depends(get_current_user),
):
    """
    Embedding-based semantic search using pgvector cosine similarity.

    In production this calls an embedding model (e.g., OpenAI text-embedding-3-small
    or a local sentence-transformers model) to vectorize the query, then queries
    the pgvector index.  In air-gap / stub mode it falls back to full-text search.
    """
    require_permission(user, "scenario:read")
    db = request.app.state.db

    # Stub: fall back to full-text search since embedding model not available
    # Production: replace with embedding = await embed(body.query)
    #   then: ORDER BY embedding <=> $embedding LIMIT $limit
    fallback_request = SearchRequest(
        q=body.query,
        source_types=body.source_types,
        classification=body.classification,
        limit=body.limit,
        offset=0,
    )
    return await search_intel(request, fallback_request, user)
