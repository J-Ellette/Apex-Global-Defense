from __future__ import annotations

"""Deterministic entity extraction engine.

Uses regex patterns and curated keyword lists to extract named entities from
intelligence text.  This provides a non-AI fallback that works fully offline
and requires no ML model weights, satisfying the AGD air-gap-first design
principle.  When an AI backend is configured, callers can layer an LLM pass
on top of these results for higher recall.
"""

import re
import time
from app.models import EntityType, ExtractedEntity, ExtractionResult

# ---------------------------------------------------------------------------
# Keyword / pattern registries
# ---------------------------------------------------------------------------

_WEAPON_KEYWORDS: frozenset[str] = frozenset({
    "IED", "VBIED", "SVBIED", "RPG", "RPG-7", "AK-47", "AK-74", "M16",
    "M4", "AR-15", "Kalashnikov", "MANPADS", "Stinger", "SA-7", "SA-24",
    "artillery", "mortar", "howitzer", "tank", "T-72", "T-80", "T-90",
    "M1 Abrams", "Leopard", "Challenger", "missile", "MLRS", "rocket",
    "grenade", "C4", "TNT", "PETN", "RDX", "Semtex", "bomb", "explosive",
    "drone", "UAV", "UAS", "Shahed", "Bayraktar", "TB2", "Switchblade",
    "helicopter", "gunship", "aircraft", "fighter jet", "F-16", "Su-35",
    "MiG", "anthrax", "sarin", "VX", "novichok", "chlorine", "mustard gas",
    "dirty bomb", "IMP", "EFP", "claymore",
})

_WEAPON_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in sorted(_WEAPON_KEYWORDS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)

_ORG_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(?:ISIS|ISIL|Daesh)\b", re.IGNORECASE),
    re.compile(r"\bAl-?Qa(?:e|i)da\b", re.IGNORECASE),
    re.compile(r"\b(?:Boko Haram|Al-Shabaab|Al Shabaab|Jabhat al-Nusra|Hayat Tahrir al-Sham|HTS)\b", re.IGNORECASE),
    re.compile(r"\b(?:Hamas|Hezbollah|Hizb(?:ullah)?|PIJ|Palestinian Islamic Jihad)\b", re.IGNORECASE),
    re.compile(r"\b(?:Taliban|Haqqani network?|Lashkar-e-Taiba|Jaish-e-Mohammed)\b", re.IGNORECASE),
    re.compile(r"\b(?:Wagner Group|Wagner PMC|Prigozhin)\b", re.IGNORECASE),
    re.compile(r"\b(?:NATO|ISAF|EUFOR|KFOR|INTERFET|UN|OSCE|IAEA)\b"),
    re.compile(r"\b(?:CIA|FBI|NSA|DIA|NGA|GCHQ|BND|FSB|SVR|GRU|Mossad|ISI|RAW|MSS)\b"),
    re.compile(r"\b(?:US Army|US Navy|USMC|USAF|USSF|Royal Air Force|RAF|SAS|Delta Force|SEAL Team|DEVGRU|Green Berets)\b", re.IGNORECASE),
    re.compile(r"\b[A-Z][a-z]+(?: [A-Z][a-z]+)* (?:Group|Organisation|Organization|Front|Movement|Alliance|Forces?|Brigade|Division|Corps|Regiment|Battalion|Militia|Junta|Council|Command)\b"),
]

_PERSON_PATTERNS: list[re.Pattern[str]] = [
    # Military/official titles followed by name
    re.compile(r"\b(?:General|Maj(?:or)?\.?-?Gen(?:eral)?|Lieutenant General|Brigadier|Colonel|Major|Captain|Admiral|Vice Admiral|Rear Admiral|Commodore|Field Marshal|Marshal)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b"),
    # Political/official titles
    re.compile(r"\b(?:President|Prime Minister|Minister|Secretary|Director|Chief of Staff|Commander|General Secretary)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b"),
    # Arabic-style names (common in MENA intel)
    re.compile(r"\b[A-Z][a-z]+(?: [A-Z][a-z]+)? (?:al|bin|bint|ibn|abu|um)-[A-Z][a-z]+\b", re.IGNORECASE),
    # Patronymic patterns (Central Asian / Eastern European)
    re.compile(r"\b[A-Z][a-z]+ov(?:ich)?\b"),
    re.compile(r"\b[A-Z][a-z]+ev(?:ich)?\b"),
]

_LOCATION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(?:north(?:ern)?|south(?:ern)?|east(?:ern)?|west(?:ern)?|central)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b", re.IGNORECASE),
    re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)? (?:province|region|district|governorate|oblast|krai|wilayat|prefecture|county|state|city|town|village|valley|border crossing|checkpoint|crossing|airport|seaport|port)\b", re.IGNORECASE),
    re.compile(r"\b(?:Baghdad|Mosul|Raqqa|Fallujah|Ramadi|Kirkuk|Kabul|Kandahar|Helmand|Kunduz|Kyiv|Kharkiv|Mariupol|Zaporizhzhia|Kherson|Donetsk|Luhansk|Damascus|Aleppo|Homs|Idlib|Deir ez-Zor|Sana'a|Aden|Hodeidah|Gaza|Rafah|Jenin|Nablus|Kabul|Jalalabad|Peshawar|Quetta|Karachi|Mogadishu|Nairobi|Bamako|Niamey|Ouagadougou|N'Djamena|Bangui|Khartoum|Juba)\b"),
    re.compile(r"\bHill\s+\d{3,4}\b"),  # Military map references (Hill 937, etc.)
    re.compile(r"\bGrid\s+[A-Z]{2}\s*\d{4,8}\b"),  # MGRS-style references
]

_EVENT_KEYWORDS: frozenset[str] = frozenset({
    "attack", "bombing", "airstrike", "air strike", "strike", "ambush", "raid",
    "assassination", "kidnapping", "abduction", "hostage", "explosion", "detonation",
    "operation", "offensive", "incursion", "skirmish", "clash", "engagement",
    "massacre", "ceasefire", "surrender", "withdrawal", "advance", "counterattack",
    "siege", "shelling", "sniper", "suicide bombing", "SVBIED attack", "IED attack",
    "VBIED attack", "rocket attack", "mortar attack", "drone strike",
})

_EVENT_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(e) for e in sorted(_EVENT_KEYWORDS, key=len, reverse=True)) + r"s?\b)",
    re.IGNORECASE,
)

_DATE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b", re.IGNORECASE),
    re.compile(r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b", re.IGNORECASE),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+\w+\s+\d{1,2}\b", re.IGNORECASE),
    re.compile(r"\b(?:yesterday|today|last\s+(?:week|month|year)|this\s+(?:week|month|morning|afternoon|evening))\b", re.IGNORECASE),
]

_FACILITY_KEYWORDS: frozenset[str] = frozenset({
    "base", "FOB", "COP", "outpost", "checkpoint", "airfield", "airport",
    "barracks", "headquarters", "HQ", "bunker", "compound", "detention center",
    "prison", "hospital", "mosque", "school", "market", "bridge", "dam",
    "power plant", "oil refinery", "pipeline", "depot", "warehouse",
    "embassy", "consulate", "parliament", "palace",
})

_FACILITY_PATTERN = re.compile(
    r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+)?(?:" +
    "|".join(re.escape(f) for f in sorted(_FACILITY_KEYWORDS, key=len, reverse=True)) +
    r")\b",
    re.IGNORECASE,
)

_VEHICLE_KEYWORDS: frozenset[str] = frozenset({
    "MRAP", "Humvee", "Stryker", "Bradley", "BMP", "BTR", "BRDM",
    "pickup truck", "technical", "suicide vehicle", "car bomb",
    "armored vehicle", "armoured vehicle", "convoy", "motorcade",
})

_VEHICLE_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(v) for v in sorted(_VEHICLE_KEYWORDS, key=len, reverse=True)) + r"s?\b)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Core extraction function
# ---------------------------------------------------------------------------

def _dedup_entities(entities: list[ExtractedEntity]) -> list[ExtractedEntity]:
    """Remove duplicate entity spans (same type + normalized text)."""
    seen: set[tuple[str, str]] = set()
    result: list[ExtractedEntity] = []
    for ent in entities:
        key = (ent.type.value, ent.text.strip().lower())
        if key not in seen:
            seen.add(key)
            result.append(ent)
    return result


def extract_entities(text: str) -> list[ExtractedEntity]:
    """Run all pattern matchers against *text* and return deduplicated entities."""
    entities: list[ExtractedEntity] = []

    # Weapons
    for m in _WEAPON_PATTERN.finditer(text):
        entities.append(ExtractedEntity(
            type=EntityType.WEAPON,
            text=m.group(0),
            confidence=0.90,
            start_char=m.start(),
            end_char=m.end(),
        ))

    # Organizations
    for pat in _ORG_PATTERNS:
        for m in pat.finditer(text):
            entities.append(ExtractedEntity(
                type=EntityType.ORGANIZATION,
                text=m.group(0),
                confidence=0.85,
                start_char=m.start(),
                end_char=m.end(),
            ))

    # Persons
    for pat in _PERSON_PATTERNS:
        for m in pat.finditer(text):
            # Avoid picking up single-word matches that are too short
            if len(m.group(0).split()) >= 2:
                entities.append(ExtractedEntity(
                    type=EntityType.PERSON,
                    text=m.group(0),
                    confidence=0.75,
                    start_char=m.start(),
                    end_char=m.end(),
                ))

    # Locations
    for pat in _LOCATION_PATTERNS:
        for m in pat.finditer(text):
            entities.append(ExtractedEntity(
                type=EntityType.LOCATION,
                text=m.group(0),
                confidence=0.80,
                start_char=m.start(),
                end_char=m.end(),
            ))

    # Events
    for m in _EVENT_PATTERN.finditer(text):
        entities.append(ExtractedEntity(
            type=EntityType.EVENT,
            text=m.group(0),
            confidence=0.70,
            start_char=m.start(),
            end_char=m.end(),
        ))

    # Dates
    for pat in _DATE_PATTERNS:
        for m in pat.finditer(text):
            entities.append(ExtractedEntity(
                type=EntityType.DATE,
                text=m.group(0),
                confidence=0.95,
                start_char=m.start(),
                end_char=m.end(),
            ))

    # Facilities
    for m in _FACILITY_PATTERN.finditer(text):
        span_text = m.group(0).strip()
        if len(span_text) > 3:
            entities.append(ExtractedEntity(
                type=EntityType.FACILITY,
                text=span_text,
                confidence=0.65,
                start_char=m.start(),
                end_char=m.end(),
            ))

    # Vehicles
    for m in _VEHICLE_PATTERN.finditer(text):
        entities.append(ExtractedEntity(
            type=EntityType.VEHICLE,
            text=m.group(0),
            confidence=0.80,
            start_char=m.start(),
            end_char=m.end(),
        ))

    return _dedup_entities(entities)


def run_extraction(text: str) -> ExtractionResult:
    """Public API: extract entities and return a result bundle with timing."""
    t0 = time.perf_counter()
    entities = extract_entities(text)
    duration_ms = (time.perf_counter() - t0) * 1000

    return ExtractionResult(
        entities=entities,
        entity_count=len(entities),
        method="deterministic",
        duration_ms=round(duration_ms, 2),
    )
