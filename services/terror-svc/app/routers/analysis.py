from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import get_current_user, require_permission
from app.data.attack_types import ATTACK_TYPE_CATALOG, ATTACK_TYPE_MAP
from app.models import (
    AttackRisk,
    CrowdDensity,
    SiteType,
    SiteVulnerabilityAnalysis,
    TerrorSite,
)
from app.routers.sites import _row_to_site

router = APIRouter(tags=["analysis"])


# ---------------------------------------------------------------------------
# Attack risk scoring per site type
# ---------------------------------------------------------------------------

# Maps site types to attack types that are most relevant (higher weight)
_SITE_ATTACK_AFFINITY: dict[SiteType, set[str]] = {
    SiteType.TRANSPORT_HUB: {"VRAM", "EXPL", "SBOM", "CHEM", "INFR"},
    SiteType.STADIUM: {"VRAM", "SBOM", "ASHT", "EXPL"},
    SiteType.GOVERNMENT_BUILDING: {"EXPL", "ASHT", "ASSN", "HSTG", "CYBR"},
    SiteType.HOTEL: {"HSTG", "EXPL", "ASHT", "ASSN"},
    SiteType.MARKET: {"VRAM", "SBOM", "EXPL", "ASHT"},
    SiteType.HOUSE_OF_WORSHIP: {"ASHT", "EXPL", "SBOM"},
    SiteType.SCHOOL: {"ASHT", "HSTG", "EXPL"},
    SiteType.HOSPITAL: {"ASHT", "BIOL", "CYBR", "HSTG"},
    SiteType.EMBASSY: {"EXPL", "ASSN", "HSTG", "ASHT", "CHEM"},
    SiteType.CRITICAL_INFRASTRUCTURE: {"INFR", "CYBR", "EXPL", "CHEM"},
    SiteType.FINANCIAL_CENTER: {"EXPL", "CYBR", "ASSN", "INFR"},
    SiteType.MILITARY_BASE: {"EXPL", "CHEM", "CYBR", "ASSN", "INFR"},
    SiteType.ENTERTAINMENT_VENUE: {"VRAM", "SBOM", "ASHT", "EXPL"},
    SiteType.SHOPPING_CENTER: {"VRAM", "SBOM", "ASHT", "EXPL"},
}


def _compute_attack_risks(site: TerrorSite) -> list[AttackRisk]:
    """
    Score each attack type against a site and return sorted by risk score.
    Risk = attack lethality weight * site vulnerability * affinity factor * crowd factor
    """
    vuln_norm = site.vulnerability_score / 10.0
    crowd_mult = {
        CrowdDensity.LOW: 0.6,
        CrowdDensity.MEDIUM: 1.0,
        CrowdDensity.HIGH: 1.3,
        CrowdDensity.CRITICAL: 1.6,
    }.get(site.crowd_density, 1.0)

    affinity_set = _SITE_ATTACK_AFFINITY.get(site.site_type, set())

    risks: list[AttackRisk] = []
    for attack in ATTACK_TYPE_CATALOG:
        # Lethality factor: normalized from catalog's avg_killed_high
        max_lethality = max(a.avg_killed_high for a in ATTACK_TYPE_CATALOG)
        lethality = attack.avg_killed_high / max_lethality if max_lethality > 0 else 0.0

        affinity = 1.4 if attack.id in affinity_set else 0.7
        raw_score = lethality * vuln_norm * affinity * crowd_mult
        risk_score = round(min(10.0, raw_score * 10.0), 2)

        # Build rationale
        if risk_score >= 7.0:
            severity = "HIGH RISK"
        elif risk_score >= 4.0:
            severity = "MODERATE RISK"
        else:
            severity = "LOW RISK"

        if attack.id in affinity_set:
            affinity_reason = f"{site.site_type.value.replace('_', ' ').title()} sites are a typical target vector for {attack.label}."
        else:
            affinity_reason = f"{attack.label} has lower historical affinity with this site type."

        vuln_reason = (
            f"Site vulnerability score {site.vulnerability_score:.1f}/10 amplifies risk."
            if site.vulnerability_score >= 6.0
            else f"Site security posture (score {site.vulnerability_score:.1f}/10) partially mitigates risk."
        )

        rationale = f"{severity}: {affinity_reason} {vuln_reason}"
        risks.append(AttackRisk(
            attack_type_id=attack.id,
            attack_type_label=attack.label,
            risk_score=risk_score,
            rationale=rationale,
        ))

    risks.sort(key=lambda x: x.risk_score, reverse=True)
    return risks


def _generate_recommendations(site: TerrorSite, top_risks: list[AttackRisk]) -> list[str]:
    """Generate actionable security recommendations for the site."""
    recs: list[str] = []

    # Dimension-specific recommendations
    if site.physical_security < 0.4:
        recs.append(
            "PHYSICAL SECURITY is critically low. Install vehicle barriers and bollards, "
            "increase guard patrols, and harden perimeter access points immediately."
        )
    elif site.physical_security < 0.6:
        recs.append(
            "PHYSICAL SECURITY should be improved. Consider additional barriers, "
            "fencing upgrades, and increased guard presence at entry points."
        )

    if site.access_control < 0.4:
        recs.append(
            "ACCESS CONTROL is inadequate. Implement mandatory screening checkpoints, "
            "ID verification, and bag searches for all entry points."
        )
    elif site.access_control < 0.6:
        recs.append(
            "ACCESS CONTROL should be strengthened. Deploy additional screening technology "
            "and ensure all access points are staffed with trained security personnel."
        )

    if site.surveillance < 0.4:
        recs.append(
            "SURVEILLANCE coverage is insufficient. Deploy CCTV across all public areas "
            "and access points. Establish a central monitoring station with trained operators."
        )
    elif site.surveillance < 0.6:
        recs.append(
            "SURVEILLANCE should be expanded. Identify coverage gaps and deploy "
            "additional cameras. Integrate with law enforcement monitoring where possible."
        )

    if site.emergency_response < 0.4:
        recs.append(
            "EMERGENCY RESPONSE capability is critically deficient. Establish an on-site "
            "first responder presence, draft an emergency response plan, and conduct "
            "regular evacuation drills with all staff."
        )
    elif site.emergency_response < 0.6:
        recs.append(
            "EMERGENCY RESPONSE readiness should be improved. Update evacuation plans, "
            "train staff in emergency procedures, and establish direct contact protocols "
            "with local police, fire, and medical services."
        )

    # Crowd density recommendations
    if site.crowd_density in (CrowdDensity.HIGH, CrowdDensity.CRITICAL):
        recs.append(
            f"CROWD DENSITY is {site.crowd_density.value}. Implement crowd management protocols, "
            "capacity monitoring, and controlled entry/exit flows to reduce mass casualty potential."
        )

    # Attack-type specific recommendations
    top_ids = {r.attack_type_id for r in top_risks[:3]}
    if "VRAM" in top_ids:
        recs.append(
            "HIGH VEHICLE RAMMING RISK: Install anti-vehicle bollards and barriers at all "
            "pedestrian access zones. Restrict vehicle access within 50m of high-density areas."
        )
    if "EXPL" in top_ids or "SBOM" in top_ids:
        recs.append(
            "HIGH EXPLOSIVE THREAT: Deploy explosive trace detection and K9 units at entry. "
            "Conduct regular security sweeps and establish clear bag-checking protocols."
        )
    if "CYBR" in top_ids or "INFR" in top_ids:
        recs.append(
            "CYBER/INFRASTRUCTURE THREAT: Harden control systems and communications. "
            "Establish offline fallback procedures and conduct regular penetration testing."
        )
    if "CHEM" in top_ids or "BIOL" in top_ids:
        recs.append(
            "CBRN THREAT: Install air monitoring sensors and seal HVAC systems. "
            "Pre-position antidote stockpiles and ensure CBRN-trained responders are available."
        )

    # Coordination recommendation
    if site.vulnerability_score >= 7.0:
        recs.append(
            f"PRIORITY SITE: With a vulnerability score of {site.vulnerability_score:.1f}/10, "
            "this site warrants immediate multi-agency coordination. "
            "Schedule a joint security review with police, fire, and relevant intelligence agencies."
        )

    if not recs:
        recs.append(
            "Site security posture is adequate. Continue regular security audits and "
            "maintain threat intelligence monitoring for emerging indicators."
        )

    return recs


# ---------------------------------------------------------------------------
# Analysis endpoint
# ---------------------------------------------------------------------------

@router.get("/terror/sites/{site_id}/analysis", response_model=SiteVulnerabilityAnalysis)
async def analyze_site(
    request: Request,
    site_id: UUID,
    user: dict = Depends(get_current_user),
):
    """
    Run full vulnerability analysis for a terror target site:
    - Vulnerability dimension breakdown
    - Attack type risk scoring (all 10 attack types)
    - Actionable security recommendations
    - Multi-agency coordination suggestions
    """
    require_permission(user, "scenario:read")
    db = request.app.state.db

    row = await db.fetchrow("SELECT * FROM terror_sites WHERE id = $1", site_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Site not found")

    site = _row_to_site(dict(row))

    attack_risks = _compute_attack_risks(site)
    top_risks = attack_risks[:5]
    recommendations = _generate_recommendations(site, top_risks)

    # Build summary
    if site.vulnerability_score >= 7.0:
        level = "HIGH VULNERABILITY"
    elif site.vulnerability_score >= 4.0:
        level = "MODERATE VULNERABILITY"
    else:
        level = "LOW VULNERABILITY"

    weakest_dim = min(
        [
            ("physical security", site.physical_security),
            ("access control", site.access_control),
            ("surveillance", site.surveillance),
            ("emergency response", site.emergency_response),
        ],
        key=lambda x: x[1],
    )
    top_threat = attack_risks[0] if attack_risks else None

    summary = (
        f"{site.name} ({site.site_type.value.replace('_', ' ').title()}) assessed as {level} "
        f"with composite score {site.vulnerability_score:.1f}/10. "
        f"Weakest dimension: {weakest_dim[0]} ({weakest_dim[1]:.0%}). "
    )
    if top_threat:
        summary += (
            f"Highest risk attack vector: {top_threat.attack_type_label} "
            f"(risk score {top_threat.risk_score:.1f}/10)."
        )

    return SiteVulnerabilityAnalysis(
        site_id=site.id,
        site_name=site.name,
        vulnerability_score=site.vulnerability_score,
        dimension_scores={
            "physical_security": round(site.physical_security, 3),
            "access_control": round(site.access_control, 3),
            "surveillance": round(site.surveillance, 3),
            "emergency_response": round(site.emergency_response, 3),
        },
        top_attack_risks=top_risks,
        recommendations=recommendations,
        analysis_summary=summary,
        metadata={
            "crowd_density": site.crowd_density.value,
            "site_type": site.site_type.value,
            "population_capacity": site.population_capacity,
        },
    )
