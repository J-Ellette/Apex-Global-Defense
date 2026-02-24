from __future__ import annotations

"""Deterministic threat assessment engine.

Implements a weighted scoring matrix (the PMESII-PT / ASCOPE inspired approach)
that computes threat scores without requiring an AI backend.  This is the
non-AI fallback guaranteed by the AGD design principles.

Scoring methodology:
  1. Parse actor / target strings for known threat actor categories.
  2. Evaluate a set of boolean threat indicators derived from the context text.
  3. Apply weights to produce a raw score 0–10.
  4. Map score → ThreatLevel enum.
  5. Select active threat vectors (MILITARY, TERRORIST, CYBER, CBRN, ECONOMIC, HYBRID).
"""

from datetime import datetime, timezone
import re

from app.models import (
    ThreatAssessmentRequest,
    ThreatAssessmentResult,
    ThreatIndicator,
    ThreatLevel,
    ThreatVector,
)

# ---------------------------------------------------------------------------
# Actor classification keywords
# ---------------------------------------------------------------------------

_TERRORIST_ACTORS = frozenset({
    "isis", "isil", "daesh", "al-qaeda", "al qaeda", "boko haram",
    "al-shabaab", "hamas", "hezbollah", "hizbullah", "taliban",
    "jabhat al-nusra", "hts", "hayat tahrir al-sham", "pij",
    "lashkar-e-taiba", "jaish-e-mohammed", "wagner", "pmc",
    "insurgent", "terrorist", "militia", "extremist", "jihadist",
})

_STATE_ACTORS = frozenset({
    "russia", "russian federation", "chinese", "china", "iran", "north korea",
    "dprk", "syria", "venezuela", "belarus",
})

_CYBER_ACTORS = frozenset({
    "apt", "fancy bear", "cozy bear", "lazarus", "sandworm",
    "charming kitten", "double dragon", "equation group",
    "hacker", "cyber", "ransomware", "malware",
})

# ---------------------------------------------------------------------------
# Indicator templates — each indicator has a weight and a set of trigger keywords
# ---------------------------------------------------------------------------

_INDICATORS: list[dict] = [
    # Military / kinetic
    {"indicator": "Armed group mobilization reported",  "weight": 1.5, "triggers": {"mobilization", "movement", "troop", "reinforcement", "advance", "repositioning"}},
    {"indicator": "Recent kinetic activity in area of interest", "weight": 2.0, "triggers": {"attack", "airstrike", "shelling", "bombing", "ambush", "explosion", "detonation"}},
    {"indicator": "Weapons cache or smuggling detected",  "weight": 1.2, "triggers": {"cache", "smuggling", "trafficking", "weapons", "arms", "ammunition"}},
    {"indicator": "IED/VBIED threat indicators present",  "weight": 1.8, "triggers": {"ied", "vbied", "svbied", "car bomb", "suicide bombing", "explosive device"}},
    # Intelligence / surveillance
    {"indicator": "Actor conducting reconnaissance",    "weight": 1.0, "triggers": {"reconnaissance", "surveillance", "observation", "intelligence gathering", "scout"}},
    {"indicator": "Foreign intelligence activity detected", "weight": 1.3, "triggers": {"spy", "espionage", "intelligence", "agent", "asset", "handler"}},
    # Cyber
    {"indicator": "Cyber intrusion or attack reported", "weight": 1.5, "triggers": {"cyber", "hack", "malware", "ransomware", "intrusion", "phishing", "apt", "breach"}},
    {"indicator": "Critical infrastructure targeted",   "weight": 1.8, "triggers": {"power grid", "water supply", "pipeline", "communications", "financial system"}},
    # CBRN
    {"indicator": "CBRN material or capability suspected", "weight": 2.5, "triggers": {"cbrn", "chemical", "biological", "radiological", "nuclear", "wmd", "sarin", "anthrax", "dirty bomb"}},
    # Destabilization
    {"indicator": "Propaganda / information operations", "weight": 0.8, "triggers": {"propaganda", "disinformation", "psyop", "influence operation", "fake news"}},
    {"indicator": "Ethnic or sectarian tensions elevated", "weight": 1.0, "triggers": {"sectarian", "ethnic", "communal", "religious tension", "tribal"}},
    {"indicator": "Leadership or command node identified", "weight": 1.0, "triggers": {"commander", "leader", "emir", "general", "head", "chief of staff"}},
    # Threat actor specific
    {"indicator": "Suicide attack methodology indicated", "weight": 2.0, "triggers": {"suicide", "martyr", "shahid", "istishhadi"}},
    {"indicator": "Hostage taking or kidnapping", "weight": 1.5, "triggers": {"hostage", "kidnap", "abduct", "ransom"}},
]


def _classify_actor(actor: str) -> tuple[bool, bool, bool]:
    """Return (is_terrorist, is_state, is_cyber) based on actor description."""
    a = actor.lower()
    is_terrorist = any(t in a for t in _TERRORIST_ACTORS)
    is_state = any(s in a for s in _STATE_ACTORS)
    is_cyber = any(c in a for c in _CYBER_ACTORS)
    return is_terrorist, is_state, is_cyber


def _evaluate_indicators(context: str) -> list[ThreatIndicator]:
    """Check each indicator against context text and return results."""
    ctx_lower = context.lower()
    results: list[ThreatIndicator] = []
    for spec in _INDICATORS:
        present = any(trigger in ctx_lower for trigger in spec["triggers"])
        results.append(ThreatIndicator(
            indicator=spec["indicator"],
            weight=spec["weight"],
            present=present,
            source="context_analysis",
        ))
    return results


def _compute_score(indicators: list[ThreatIndicator]) -> float:
    """Sum weighted active indicators, normalize to 0–10."""
    max_score = sum(i.weight for i in indicators)
    raw = sum(i.weight for i in indicators if i.present)
    if max_score == 0:
        return 0.0
    return round(min(10.0, (raw / max_score) * 10.0 * 1.5), 2)


def _score_to_level(score: float) -> ThreatLevel:
    if score >= 8.0:
        return ThreatLevel.CRITICAL
    if score >= 6.0:
        return ThreatLevel.HIGH
    if score >= 4.0:
        return ThreatLevel.MODERATE
    if score >= 2.0:
        return ThreatLevel.LOW
    return ThreatLevel.NEGLIGIBLE


def _derive_vectors(
    indicators: list[ThreatIndicator],
    is_terrorist: bool,
    is_state: bool,
    is_cyber: bool,
) -> list[ThreatVector]:
    active = {i.indicator for i in indicators if i.present}
    vectors: list[ThreatVector] = []

    if any("kinetic" in i.lower() or "IED" in i or "mobilization" in i for i in active):
        vectors.append(ThreatVector.MILITARY if is_state else ThreatVector.TERRORIST)

    if is_cyber or any("cyber" in i.lower() or "infrastructure" in i.lower() for i in active):
        vectors.append(ThreatVector.CYBER)

    if any("CBRN" in i for i in active):
        vectors.append(ThreatVector.CBRN)

    if is_state and any("propaganda" in i.lower() or "sectarian" in i.lower() for i in active):
        vectors.append(ThreatVector.HYBRID)

    if not vectors:
        vectors = [ThreatVector.MILITARY] if is_state else [ThreatVector.TERRORIST]

    return list(dict.fromkeys(vectors))  # preserve order, deduplicate


def _build_summary(
    actor: str,
    target: str,
    level: ThreatLevel,
    score: float,
    vectors: list[ThreatVector],
    confidence: float,
) -> str:
    vector_str = ", ".join(v.value for v in vectors)
    return (
        f"{actor} poses a {level.value} threat to {target} (score {score:.1f}/10). "
        f"Primary threat vectors: {vector_str}. "
        f"Assessment confidence: {confidence:.0%}."
    )


def _build_recommendations(
    level: ThreatLevel,
    vectors: list[ThreatVector],
    is_terrorist: bool,
    is_state: bool,
) -> list[str]:
    recs: list[str] = []

    if level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
        recs.append(
            "IMMEDIATE ACTION: Elevate force protection posture and brief all personnel "
            "on current threat indicators."
        )

    if ThreatVector.MILITARY in vectors:
        if is_state:
            recs.append(
                "Reinforce defensive positions, increase ISR coverage, and coordinate "
                "with allied forces for mutual support."
            )
        else:
            recs.append(
                "Increase patrol frequency and checkpoint screening. "
                "Implement strict access control around key assets."
            )

    if ThreatVector.TERRORIST in vectors or is_terrorist:
        recs.append(
            "Harden soft targets, increase random security patrols, and establish "
            "rapid response protocols for mass casualty events."
        )

    if ThreatVector.CYBER in vectors:
        recs.append(
            "Audit network access controls, segment critical systems, and activate "
            "24/7 SOC monitoring. Prepare for comms degradation."
        )

    if ThreatVector.CBRN in vectors:
        recs.append(
            "Issue CBRN warning to all units. Pre-position detection equipment and "
            "decontamination assets. Ensure medical personnel are CBRN-qualified."
        )

    if ThreatVector.HYBRID in vectors:
        recs.append(
            "Counter disinformation by proactively publishing factual reporting. "
            "Monitor social media for coordinated influence campaigns."
        )

    if not recs:
        recs.append(
            "Continue routine monitoring and threat reporting. No immediate protective "
            "action required at current threat level."
        )

    return recs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def assess_threat(request: ThreatAssessmentRequest) -> ThreatAssessmentResult:
    """Run deterministic threat assessment and return a scored result."""
    context = " ".join(filter(None, [request.actor, request.target, request.context or ""]))

    is_terrorist, is_state, is_cyber = _classify_actor(request.actor)
    indicators = _evaluate_indicators(context)
    score = _compute_score(indicators)

    # Actor type modifier: state actors and known terror orgs start with higher baseline
    if is_state:
        score = min(10.0, score + 1.0)
    if is_terrorist:
        score = min(10.0, score + 1.5)

    level = _score_to_level(score)
    vectors = _derive_vectors(indicators, is_terrorist, is_state, is_cyber)

    # Confidence: higher when more indicators are present
    active_count = sum(1 for i in indicators if i.present)
    confidence = round(min(0.95, 0.4 + (active_count / len(indicators)) * 0.6), 2)

    summary = _build_summary(request.actor, request.target, level, score, vectors, confidence)
    recommendations = _build_recommendations(level, vectors, is_terrorist, is_state)

    return ThreatAssessmentResult(
        actor=request.actor,
        target=request.target,
        threat_level=level,
        threat_score=score,
        threat_vectors=vectors,
        indicators=indicators,
        confidence=confidence,
        summary=summary,
        recommendations=recommendations,
        assessed_at=datetime.now(tz=timezone.utc),
        ai_assisted=False,
    )
