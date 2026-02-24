from __future__ import annotations

"""OSINT ingestion adapter stubs.

Each adapter follows the OSINTAdapter interface.  In production these would
call live APIs (ACLED, UCDP, public RSS feeds).  In development / air-gap
mode they return deterministic synthetic data so the pipeline can be tested
end-to-end without network access.

Adapters are keyed by source_id.  The OSINT router calls `run_ingestion()`
which dispatches to the correct adapter, saves items to the DB, and records
job metadata.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import AsyncIterator
from uuid import uuid4

import httpx

from app.models import IngestRequest, IngestResult, OSINTSource, OSINTSourceStatus, OSINTSourceType, SourceType


# ---------------------------------------------------------------------------
# Adapter base class
# ---------------------------------------------------------------------------

class OSINTAdapter(ABC):
    source_id: str
    source_type: OSINTSourceType

    @abstractmethod
    async def fetch(
        self,
        since: datetime,
        max_items: int,
    ) -> AsyncIterator[dict]:
        """Yield raw intel item dicts ready for DB insertion."""
        ...  # pragma: no cover

    def get_source_info(self) -> OSINTSource:
        return OSINTSource(
            id=self.source_id,
            name=self.source_id.replace("_", " ").title(),
            source_type=self.source_type,
            status=OSINTSourceStatus.ACTIVE,
        )


# ---------------------------------------------------------------------------
# ACLED adapter (Armed Conflict Location & Event Data)
# ---------------------------------------------------------------------------

class ACLEDAdapter(OSINTAdapter):
    source_id = "acled"
    source_type = OSINTSourceType.ACLED

    def __init__(self, api_key: str = "", email: str = ""):
        self.api_key = api_key
        self.email = email

    async def fetch(self, since: datetime, max_items: int) -> AsyncIterator[dict]:
        if not self.api_key or not self.email:
            # Return synthetic data when not configured
            async for item in _synthetic_acled(since, max_items):
                yield item
            return

        # Live ACLED API call
        params = {
            "key": self.api_key,
            "email": self.email,
            "event_date": since.strftime("%Y-%m-%d"),
            "event_date_where": ">=",
            "limit": max_items,
            "fields": "event_id_cnty|event_type|sub_event_type|actor1|actor2|country|location|latitude|longitude|event_date|notes|fatalities",
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.get("https://api.acleddata.com/acled/read", params=params)
                r.raise_for_status()
                data = r.json().get("data", [])
        except Exception:
            # Fall back to synthetic on any error
            async for item in _synthetic_acled(since, max_items):
                yield item
            return

        for row in data[:max_items]:
            try:
                lat = float(row.get("latitude") or 0)
                lon = float(row.get("longitude") or 0)
                yield {
                    "id": str(uuid4()),
                    "source_type": SourceType.OSINT,
                    "source_url": f"https://acleddata.com/data/{row.get('event_id_cnty', '')}",
                    "title": f"{row.get('event_type', 'Event')} — {row.get('location', '')}, {row.get('country', '')}",
                    "content": row.get("notes", "No details available."),
                    "language": "eng",
                    "latitude": lat if lat != 0 else None,
                    "longitude": lon if lon != 0 else None,
                    "entities": [],
                    "classification": "UNCLASS",
                    "reliability": "C",  # ACLED is a reputable source
                    "credibility": "2",
                    "published_at": row.get("event_date"),
                }
            except (ValueError, KeyError):
                continue


async def _synthetic_acled(since: datetime, max_items: int) -> AsyncIterator[dict]:
    """Deterministic synthetic ACLED-style records for development use."""
    _EVENTS = [
        {
            "title": "Armed clash reported — Donetsk Oblast, Ukraine",
            "content": (
                "Ukrainian Armed Forces exchanged artillery fire with Russian-backed forces "
                "near the Donetsk frontline. One T-72 tank was observed maneuvering east of "
                "Bakhmut before the engagement. No confirmed casualties reported at this time."
            ),
            "latitude": 48.60, "longitude": 37.85,
        },
        {
            "title": "IED detonation — Helmand Province, Afghanistan",
            "content": (
                "A VBIED detonated at a checkpoint in Lashkar Gah, Helmand Province. "
                "The Taliban claimed responsibility. Three security personnel were killed "
                "and seven wounded. A secondary device was later discovered and safely detonated."
            ),
            "latitude": 31.59, "longitude": 64.37,
        },
        {
            "title": "Airstrike — Idlib Governorate, Syria",
            "content": (
                "Russian Air Force aircraft conducted an airstrike targeting an HTS-controlled "
                "compound in southern Idlib. The facility was suspected to house a weapons cache "
                "including mortars and RPG-7 launchers. Civilian casualties unconfirmed."
            ),
            "latitude": 35.92, "longitude": 36.63,
        },
        {
            "title": "Militant attack on convoy — Bamako, Mali",
            "content": (
                "A JNIM-affiliated militia ambushed a French Barkhane Force logistics convoy "
                "on the RN6 highway north of Bamako. Two armored vehicles were disabled. "
                "Attackers were repelled. Wagner Group advisors were reportedly present."
            ),
            "latitude": 12.65, "longitude": -8.00,
        },
        {
            "title": "Rocket attack — Baghdad, Iraq",
            "content": (
                "Katyusha rockets were fired toward the International Zone in Baghdad. "
                "The attack, attributed to Iran-backed militia groups including Kataib Hezbollah, "
                "landed near the US Embassy compound. No casualties reported."
            ),
            "latitude": 33.34, "longitude": 44.40,
        },
    ]
    base_date = since
    for i, ev in enumerate(_EVENTS[:max_items]):
        yield {
            "id": str(uuid4()),
            "source_type": SourceType.OSINT,
            "source_url": f"https://acleddata.com/synthetic/{i+1}",
            "title": ev["title"],
            "content": ev["content"],
            "language": "eng",
            "latitude": ev["latitude"],
            "longitude": ev["longitude"],
            "entities": [],
            "classification": "UNCLASS",
            "reliability": "C",
            "credibility": "2",
            "published_at": (base_date + timedelta(days=i)).isoformat(),
        }


# ---------------------------------------------------------------------------
# UCDP adapter (Uppsala Conflict Data Program)
# ---------------------------------------------------------------------------

class UCDPAdapter(OSINTAdapter):
    source_id = "ucdp"
    source_type = OSINTSourceType.UCDP

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    async def fetch(self, since: datetime, max_items: int) -> AsyncIterator[dict]:
        # UCDP API is publicly accessible; use synthetic fallback for air-gap environments
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.get(
                    "https://ucdpapi.pcr.uu.se/api/gedevents/23.1",
                    params={
                        "pagesize": min(max_items, 100),
                        "StartDate": since.strftime("%Y-%m-%d"),
                    },
                )
                r.raise_for_status()
                records = r.json().get("Result", [])
        except Exception:
            async for item in _synthetic_ucdp(since, max_items):
                yield item
            return

        for row in records[:max_items]:
            try:
                yield {
                    "id": str(uuid4()),
                    "source_type": SourceType.OSINT,
                    "source_url": f"https://ucdp.uu.se/event/{row.get('id', '')}",
                    "title": f"Armed conflict event — {row.get('country', '')}, {row.get('year', '')}",
                    "content": row.get("source_article", "") or row.get("where_description", ""),
                    "language": "eng",
                    "latitude": float(row["latitude"]) if row.get("latitude") else None,
                    "longitude": float(row["longitude"]) if row.get("longitude") else None,
                    "entities": [],
                    "classification": "UNCLASS",
                    "reliability": "B",
                    "credibility": "2",
                    "published_at": row.get("date_start"),
                }
            except (ValueError, KeyError):
                continue


async def _synthetic_ucdp(since: datetime, max_items: int) -> AsyncIterator[dict]:
    _EVENTS = [
        {
            "title": "State-based armed conflict — Tigray Region, Ethiopia",
            "content": (
                "UCDP records government forces engaged Tigray People's Liberation Front (TPLF) "
                "units near Shire, Tigray. Heavy artillery usage was reported. Estimated "
                "fatalities: 12. Source: local media reports cross-referenced with satellite imagery."
            ),
            "latitude": 14.10, "longitude": 38.28,
        },
        {
            "title": "Non-state armed group attack — Cabo Delgado, Mozambique",
            "content": (
                "UCDP records an Ansar al-Sunna (Islamist militant) attack on the village of "
                "Mocímboa da Praia, Cabo Delgado Province. Insurgents used machetes and small arms. "
                "Estimated fatalities: 5 civilians. Village was burned."
            ),
            "latitude": -11.33, "longitude": 40.35,
        },
    ]
    base_date = since
    for i, ev in enumerate(_EVENTS[:max_items]):
        yield {
            "id": str(uuid4()),
            "source_type": SourceType.OSINT,
            "source_url": f"https://ucdp.uu.se/synthetic/{i+1}",
            "title": ev["title"],
            "content": ev["content"],
            "language": "eng",
            "latitude": ev["latitude"],
            "longitude": ev["longitude"],
            "entities": [],
            "classification": "UNCLASS",
            "reliability": "B",
            "credibility": "2",
            "published_at": (base_date + timedelta(days=i)).isoformat(),
        }


# ---------------------------------------------------------------------------
# RSS adapter (generic RSS/Atom feed)
# ---------------------------------------------------------------------------

_DEFAULT_RSS_FEEDS = [
    {
        "id": "rss_reuters_world",
        "name": "Reuters World News",
        "url": "https://feeds.reuters.com/reuters/worldNews",
    },
    {
        "id": "rss_bbc_world",
        "name": "BBC World News",
        "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
    },
    {
        "id": "rss_reliefweb",
        "name": "ReliefWeb Alerts",
        "url": "https://reliefweb.int/updates/rss.xml",
    },
]


class RSSAdapter(OSINTAdapter):
    source_id = "rss"
    source_type = OSINTSourceType.RSS

    def __init__(self, feeds: list[dict] | None = None):
        self.feeds = feeds or _DEFAULT_RSS_FEEDS

    async def fetch(self, since: datetime, max_items: int) -> AsyncIterator[dict]:
        # RSS parsing requires feedparser; fall back to synthetic if unavailable
        try:
            import feedparser  # type: ignore[import-untyped]
        except ImportError:
            async for item in _synthetic_rss(since, max_items):
                yield item
            return

        fetched = 0
        for feed_cfg in self.feeds:
            if fetched >= max_items:
                break
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    r = await client.get(feed_cfg["url"])
                    feed = feedparser.parse(r.text)
            except Exception:
                continue

            for entry in feed.entries:
                if fetched >= max_items:
                    break
                pub = entry.get("published_parsed")
                pub_dt = datetime(*pub[:6], tzinfo=timezone.utc) if pub else since
                if pub_dt < since:
                    continue
                yield {
                    "id": str(uuid4()),
                    "source_type": SourceType.OSINT,
                    "source_url": entry.get("link"),
                    "title": entry.get("title", "No title"),
                    "content": entry.get("summary", entry.get("description", "")),
                    "language": "eng",
                    "latitude": None,
                    "longitude": None,
                    "entities": [],
                    "classification": "UNCLASS",
                    "reliability": "D",
                    "credibility": "4",
                    "published_at": pub_dt.isoformat(),
                }
                fetched += 1


async def _synthetic_rss(since: datetime, max_items: int) -> AsyncIterator[dict]:
    _ITEMS = [
        {
            "title": "UN report warns of escalating violence in South Sudan",
            "content": (
                "The United Nations Mission in South Sudan (UNMISS) issued a warning "
                "citing increased attacks by armed groups in Jonglei State. "
                "Approximately 50,000 civilians are at risk of displacement."
            ),
        },
        {
            "title": "Cyber intrusion targets NATO member infrastructure",
            "content": (
                "A sophisticated APT group linked to Russian intelligence conducted "
                "a spear-phishing campaign against energy sector targets in Poland. "
                "The malware used bears signatures consistent with Sandworm tools."
            ),
        },
    ]
    for i, item in enumerate(_ITEMS[:max_items]):
        yield {
            "id": str(uuid4()),
            "source_type": SourceType.OSINT,
            "source_url": f"https://synthetic-rss/item/{i+1}",
            "title": item["title"],
            "content": item["content"],
            "language": "eng",
            "latitude": None,
            "longitude": None,
            "entities": [],
            "classification": "UNCLASS",
            "reliability": "D",
            "credibility": "4",
            "published_at": since.isoformat(),
        }


# ---------------------------------------------------------------------------
# Adapter registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, OSINTAdapter] = {}


def _init_registry(acled_key: str = "", acled_email: str = "", ucdp_key: str = "") -> None:
    _REGISTRY["acled"] = ACLEDAdapter(api_key=acled_key, email=acled_email)
    _REGISTRY["ucdp"] = UCDPAdapter(api_key=ucdp_key)
    _REGISTRY["rss"] = RSSAdapter()


def get_adapter(source_id: str) -> OSINTAdapter | None:
    return _REGISTRY.get(source_id)


def list_adapters() -> list[OSINTAdapter]:
    return list(_REGISTRY.values())


# ---------------------------------------------------------------------------
# Ingestion runner
# ---------------------------------------------------------------------------

async def run_ingestion(
    request: IngestRequest,
    db,
    auto_extract: bool = True,
) -> IngestResult:
    """
    Fetch items from the specified adapter and insert them into the DB.
    Returns a summary of the ingestion job.
    """
    from datetime import timedelta
    from app.engine.extractor import extract_entities

    adapter = get_adapter(request.source_id)
    if adapter is None:
        return IngestResult(
            source_id=request.source_id,
            source_type=OSINTSourceType.MANUAL,
            items_fetched=0,
            items_saved=0,
            errors=[f"Unknown source: {request.source_id}"],
            dry_run=request.dry_run,
            duration_seconds=0.0,
        )

    since = datetime.now(tz=timezone.utc) - timedelta(days=request.since_days)
    t0 = time.perf_counter()
    errors: list[str] = []
    items_fetched = 0
    items_saved = 0

    async for raw in adapter.fetch(since=since, max_items=request.max_items):
        items_fetched += 1

        if request.dry_run:
            items_saved += 1
            continue

        # Auto-extract entities
        entities = []
        if auto_extract:
            try:
                entities = extract_entities(raw.get("content", ""))
                entities_json = [
                    {"type": e.type, "text": e.text, "confidence": e.confidence}
                    for e in entities
                ]
            except Exception as exc:
                entities_json = []
                errors.append(f"Entity extraction error on item {items_fetched}: {exc}")
        else:
            entities_json = raw.get("entities", [])

        try:
            import json

            lat = raw.get("latitude")
            lon = raw.get("longitude")
            location_wkt = f"POINT({lon} {lat})" if lat is not None and lon is not None else None

            await db.execute(
                """
                INSERT INTO intel_items (
                    id, source_type, source_url, title, content, language,
                    location, entities, classification, reliability, credibility,
                    published_at, ingested_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6,
                    ST_GeomFromText($7, 4326),
                    $8::jsonb, $9::classification_level, $10, $11,
                    $12, NOW()
                )
                ON CONFLICT DO NOTHING
                """,
                raw.get("id", str(uuid4())),
                raw.get("source_type", SourceType.OSINT).value
                if hasattr(raw.get("source_type"), "value")
                else str(raw.get("source_type", "OSINT")),
                raw.get("source_url"),
                raw.get("title"),
                raw.get("content"),
                raw.get("language", "eng"),
                location_wkt,
                json.dumps(entities_json),
                raw.get("classification", "UNCLASS"),
                raw.get("reliability", "F"),
                raw.get("credibility", "6"),
                raw.get("published_at"),
            )
            items_saved += 1
        except Exception as exc:
            errors.append(f"DB insert error on item {items_fetched}: {exc}")

    duration = time.perf_counter() - t0

    return IngestResult(
        source_id=request.source_id,
        source_type=adapter.source_type,
        items_fetched=items_fetched,
        items_saved=items_saved,
        errors=errors,
        dry_run=request.dry_run,
        duration_seconds=round(duration, 3),
    )
