from __future__ import annotations

"""Deterministic narrative threat analysis engine."""

import math
from uuid import UUID

from app.models import NarrativeAnalysis


def analyze_narrative(narrative: dict) -> NarrativeAnalysis:
    """
    Perform deterministic analysis of a narrative threat.

    All calculations are based solely on the narrative's attributes
    with no external dependencies or randomness.
    """
    narrative_id = narrative["id"]
    threat_level = narrative.get("threat_level", "MEDIUM")
    spread_velocity = float(narrative.get("spread_velocity", 0.5))
    reach_estimate = int(narrative.get("reach_estimate", 0))
    platforms = narrative.get("platforms", [])
    counter_narratives = narrative.get("counter_narratives", [])

    # spread_score: combine velocity with platform breadth (0-1)
    platform_count = len(platforms) if isinstance(platforms, list) else 0
    platform_factor = min(platform_count / 8.0, 1.0)  # max 8 platform types
    spread_score = round((spread_velocity * 0.7) + (platform_factor * 0.3), 4)

    # virality_index: log scale of reach_estimate, capped at 1.0
    # log10(1e9) ~= 9, so divide by 9 to normalise
    if reach_estimate > 0:
        virality_index = round(min(math.log10(reach_estimate) / 9.0, 1.0), 4)
    else:
        virality_index = 0.0

    # counter_effectiveness: based on how many counter-narratives exist
    # Assume 5+ counter-narratives = full effectiveness
    cn_count = len(counter_narratives) if isinstance(counter_narratives, list) else 0
    counter_effectiveness = round(min(cn_count / 5.0, 1.0), 4)

    # recommended_actions based on threat_level and platforms
    recommended_actions: list[str] = []
    if threat_level in ("CRITICAL", "HIGH"):
        recommended_actions.append("Escalate to senior IO officer for immediate review")
        recommended_actions.append("Coordinate counter-narrative campaign across affected platforms")
    if threat_level == "CRITICAL":
        recommended_actions.append("Brief national security leadership within 24 hours")
        recommended_actions.append("Request emergency platform takedown through diplomatic channels")
    if platform_count > 3:
        recommended_actions.append("Deploy cross-platform monitoring and flagging")
    if "STATE_MEDIA" in [str(p) for p in platforms]:
        recommended_actions.append("Engage foreign broadcast regulatory bodies")
    if "SOCIAL_MEDIA" in [str(p) for p in platforms]:
        recommended_actions.append("Alert social media trust-and-safety teams")
    if cn_count == 0:
        recommended_actions.append("Develop and publish authoritative counter-narratives")
    if spread_velocity > 0.7:
        recommended_actions.append("Activate rapid-response communications team")
    if not recommended_actions:
        recommended_actions.append("Continue monitoring and update assessment weekly")

    # risk_level maps directly from threat_level
    risk_map = {
        "CRITICAL": "CRITICAL",
        "HIGH": "HIGH",
        "MEDIUM": "MEDIUM",
        "LOW": "LOW",
    }
    risk_level = risk_map.get(threat_level, "MEDIUM")

    return NarrativeAnalysis(
        narrative_id=UUID(str(narrative_id)),
        spread_score=spread_score,
        virality_index=virality_index,
        counter_effectiveness=counter_effectiveness,
        recommended_actions=recommended_actions,
        risk_level=risk_level,
    )
