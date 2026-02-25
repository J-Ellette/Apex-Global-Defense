from __future__ import annotations

"""
Deterministic economic impact engine.

All calculations are based on simple additive formulas so results are
reproducible without any external dependencies (air-gap compatible).
"""

# GDP impact contribution per sanction type (percentage points)
_GDP_IMPACT: dict[str, float] = {
    "TRADE_EMBARGO":    2.5,
    "FINANCIAL_CUTOFF": 2.0,
    "SECTORAL":         1.8,
    "ASSET_FREEZE":     1.5,
    "ARMS_EMBARGO":     0.8,
    "TECH_TRANSFER":    0.7,
    "TRAVEL_BAN":       0.2,
    "INDIVIDUAL":       0.1,
}

# Inflation change contribution per sanction type (percentage points)
_INFLATION_IMPACT: dict[str, float] = {
    "TRADE_EMBARGO":    1.8,
    "FINANCIAL_CUTOFF": 1.2,
    "SECTORAL":         1.0,
    "ASSET_FREEZE":     0.8,
    "ARMS_EMBARGO":     0.3,
    "TECH_TRANSFER":    0.4,
    "TRAVEL_BAN":       0.1,
    "INDIVIDUAL":       0.05,
}

# Unemployment change contribution (percentage points)
_UNEMPLOYMENT_IMPACT: dict[str, float] = {
    "TRADE_EMBARGO":    1.2,
    "FINANCIAL_CUTOFF": 0.9,
    "SECTORAL":         1.0,
    "ASSET_FREEZE":     0.6,
    "ARMS_EMBARGO":     0.4,
    "TECH_TRANSFER":    0.3,
    "TRAVEL_BAN":       0.1,
    "INDIVIDUAL":       0.02,
}

# Currency devaluation contribution (percentage points)
_CURRENCY_IMPACT: dict[str, float] = {
    "TRADE_EMBARGO":    3.0,
    "FINANCIAL_CUTOFF": 4.0,
    "SECTORAL":         2.0,
    "ASSET_FREEZE":     2.5,
    "ARMS_EMBARGO":     0.5,
    "TECH_TRANSFER":    0.8,
    "TRAVEL_BAN":       0.2,
    "INDIVIDUAL":       0.05,
}

# Trade volume reduction contribution (percentage points)
_TRADE_VOLUME_IMPACT: dict[str, float] = {
    "TRADE_EMBARGO":    8.0,
    "FINANCIAL_CUTOFF": 4.0,
    "SECTORAL":         5.0,
    "ASSET_FREEZE":     2.0,
    "ARMS_EMBARGO":     2.5,
    "TECH_TRANSFER":    1.5,
    "TRAVEL_BAN":       0.5,
    "INDIVIDUAL":       0.1,
}

# Sectors affected per sanction type
_AFFECTED_SECTORS: dict[str, list[str]] = {
    "TRADE_EMBARGO":    ["manufacturing", "agriculture", "retail"],
    "FINANCIAL_CUTOFF": ["banking", "finance", "real_estate"],
    "SECTORAL":         ["energy", "mining", "heavy_industry"],
    "ASSET_FREEZE":     ["banking", "sovereign_wealth"],
    "ARMS_EMBARGO":     ["defense", "aerospace"],
    "TECH_TRANSFER":    ["technology", "research", "telecommunications"],
    "TRAVEL_BAN":       ["tourism", "hospitality"],
    "INDIVIDUAL":       [],
}

# Timeline estimate (months) per sanction type
_TIMELINE_MONTHS: dict[str, int] = {
    "TRADE_EMBARGO":    18,
    "FINANCIAL_CUTOFF": 12,
    "SECTORAL":         24,
    "ASSET_FREEZE":     6,
    "ARMS_EMBARGO":     36,
    "TECH_TRANSFER":    30,
    "TRAVEL_BAN":       3,
    "INDIVIDUAL":       1,
}

# Severity thresholds based on cumulative GDP impact (percentage points)
_SEVERITY_THRESHOLDS = [
    (15.0, "CATASTROPHIC"),
    (8.0,  "SEVERE"),
    (4.0,  "MODERATE"),
    (1.0,  "LIMITED"),
    (0.0,  "NEGLIGIBLE"),
]


def calculate_economic_impact(
    target_country: str,
    sanctions: list[dict],
    indicators: list[dict],
) -> dict:
    """
    Calculate deterministic economic impact given a list of sanction dicts and
    optional indicator dicts for the target country.

    Each sanction dict must have at minimum a ``sanction_type`` key.

    Returns a dict with all computed impact metrics plus severity and confidence.
    """
    gdp_impact = 0.0
    inflation_change = 0.0
    unemployment_change = 0.0
    currency_devaluation = 0.0
    trade_volume_reduction = 0.0
    affected_sectors: set[str] = set()
    max_timeline = 0

    for sanction in sanctions:
        s_type = sanction.get("sanction_type", "")
        gdp_impact += _GDP_IMPACT.get(s_type, 0.0)
        inflation_change += _INFLATION_IMPACT.get(s_type, 0.0)
        unemployment_change += _UNEMPLOYMENT_IMPACT.get(s_type, 0.0)
        currency_devaluation += _CURRENCY_IMPACT.get(s_type, 0.0)
        trade_volume_reduction += _TRADE_VOLUME_IMPACT.get(s_type, 0.0)
        affected_sectors.update(_AFFECTED_SECTORS.get(s_type, []))
        max_timeline = max(max_timeline, _TIMELINE_MONTHS.get(s_type, 0))

    # Apply a small GDP-baseline modifier if indicators are available
    gdp_baseline = _get_indicator(indicators, target_country, "GDP_GROWTH_RATE")
    if gdp_baseline is not None:
        # Sanctions compound against a weakening baseline
        if gdp_baseline < 0:
            gdp_impact *= 1.1

    # Determine severity
    severity = "NEGLIGIBLE"
    for threshold, label in _SEVERITY_THRESHOLDS:
        if gdp_impact >= threshold:
            severity = label
            break

    # Confidence score: higher when more indicator data is available
    indicator_count = len([i for i in indicators if i.get("country_code") == target_country])
    confidence = min(0.5 + indicator_count * 0.1, 0.95)
    if not sanctions:
        confidence = 0.0

    return {
        "gdp_impact_pct": round(gdp_impact, 2),
        "inflation_rate_change": round(inflation_change, 2),
        "unemployment_change": round(unemployment_change, 2),
        "currency_devaluation_pct": round(currency_devaluation, 2),
        "trade_volume_reduction_pct": round(trade_volume_reduction, 2),
        "affected_sectors": sorted(affected_sectors),
        "severity": severity,
        "timeline_months": max_timeline if max_timeline > 0 else 1,
        "confidence_score": round(confidence, 2),
    }


def _get_indicator(indicators: list[dict], country_code: str, name: str) -> float | None:
    for ind in indicators:
        if ind.get("country_code") == country_code and ind.get("indicator_name") == name:
            try:
                return float(ind["value"])
            except (KeyError, TypeError, ValueError):
                return None
    return None
