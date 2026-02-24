from __future__ import annotations

from app.models import CellFunction, CellStructure, CellTypeEntry

# ---------------------------------------------------------------------------
# Cell Function Catalog — describes the operational role of a cell
# ---------------------------------------------------------------------------

CELL_FUNCTION_CATALOG: list[CellTypeEntry] = [
    CellTypeEntry(
        id="CMD",
        function=CellFunction.COMMAND,
        label="Command Cell",
        description=(
            "Senior leadership cell responsible for strategic direction, target selection, "
            "and resource allocation across the network. Highest-value interdiction target."
        ),
        typical_size_min=2,
        typical_size_max=6,
        detection_difficulty="HIGH",
        interdiction_priority=10,
        icon="⭐",
        color_hex="#DC2626",
    ),
    CellTypeEntry(
        id="OPS",
        function=CellFunction.OPERATIONS,
        label="Operations Cell",
        description=(
            "Executes direct action missions including ambushes, bombings, and raids. "
            "Trained fighters with weapons and IED assembly capability."
        ),
        typical_size_min=4,
        typical_size_max=12,
        detection_difficulty="MEDIUM",
        interdiction_priority=9,
        icon="⚔️",
        color_hex="#B91C1C",
    ),
    CellTypeEntry(
        id="LOG",
        function=CellFunction.LOGISTICS,
        label="Logistics Cell",
        description=(
            "Manages supply chains for weapons, explosives, food, and money. "
            "Operates safe houses and caches. Critical network enabler."
        ),
        typical_size_min=3,
        typical_size_max=8,
        detection_difficulty="MEDIUM",
        interdiction_priority=8,
        icon="📦",
        color_hex="#D97706",
    ),
    CellTypeEntry(
        id="INT",
        function=CellFunction.INTELLIGENCE,
        label="Intelligence Cell",
        description=(
            "Conducts surveillance, route reconnaissance, and target analysis. "
            "May include informants and technical surveillance operators."
        ),
        typical_size_min=2,
        typical_size_max=6,
        detection_difficulty="HIGH",
        interdiction_priority=8,
        icon="🔍",
        color_hex="#7C3AED",
    ),
    CellTypeEntry(
        id="FIN",
        function=CellFunction.FINANCE,
        label="Finance Cell",
        description=(
            "Manages fundraising, money laundering, and distribution of funds. "
            "Often interfaces with criminal networks and hawala brokers."
        ),
        typical_size_min=2,
        typical_size_max=5,
        detection_difficulty="HIGH",
        interdiction_priority=7,
        icon="💰",
        color_hex="#059669",
    ),
    CellTypeEntry(
        id="REC",
        function=CellFunction.RECRUITMENT,
        label="Recruitment Cell",
        description=(
            "Identifies, radicalizes, and recruits new members. Operates in mosques, "
            "prisons, online spaces, and diaspora communities."
        ),
        typical_size_min=2,
        typical_size_max=8,
        detection_difficulty="MEDIUM",
        interdiction_priority=6,
        icon="🎯",
        color_hex="#2563EB",
    ),
    CellTypeEntry(
        id="PROP",
        function=CellFunction.PROPAGANDA,
        label="Propaganda Cell",
        description=(
            "Produces and disseminates propaganda, claims attacks, and manages "
            "the organization's information operations and narrative shaping."
        ),
        typical_size_min=1,
        typical_size_max=5,
        detection_difficulty="MEDIUM",
        interdiction_priority=5,
        icon="📢",
        color_hex="#0891B2",
    ),
    CellTypeEntry(
        id="SFH",
        function=CellFunction.SAFE_HOUSE,
        label="Safe House / Logistics Node",
        description=(
            "Provides refuge, meeting space, and caching for the network. "
            "Often operated by sympathizers with minimal direct involvement."
        ),
        typical_size_min=1,
        typical_size_max=4,
        detection_difficulty="LOW",
        interdiction_priority=6,
        icon="🏠",
        color_hex="#6B7280",
    ),
    CellTypeEntry(
        id="MED",
        function=CellFunction.MEDICAL,
        label="Medical Support Cell",
        description=(
            "Provides medical care to wounded fighters. Operates clandestinely "
            "through sympathetic medical personnel or captured supplies."
        ),
        typical_size_min=1,
        typical_size_max=4,
        detection_difficulty="LOW",
        interdiction_priority=4,
        icon="🏥",
        color_hex="#10B981",
    ),
    CellTypeEntry(
        id="TECH",
        function=CellFunction.TECHNICAL,
        label="Technical / IED Cell",
        description=(
            "Specializes in IED construction, electronics, and improvised weapons. "
            "Often contains bomb-makers with advanced technical skills."
        ),
        typical_size_min=1,
        typical_size_max=4,
        detection_difficulty="MEDIUM",
        interdiction_priority=9,
        icon="🔧",
        color_hex="#F59E0B",
    ),
]

CELL_FUNCTION_MAP: dict[str, CellTypeEntry] = {e.id: e for e in CELL_FUNCTION_CATALOG}


# ---------------------------------------------------------------------------
# Cell Structure Descriptions
# ---------------------------------------------------------------------------

STRUCTURE_DESCRIPTIONS: dict[CellStructure, str] = {
    CellStructure.HIERARCHICAL: (
        "Traditional top-down command structure. Command cells control operational cells directly. "
        "Highly coordinated but vulnerable to decapitation strikes."
    ),
    CellStructure.NETWORK: (
        "Flat, peer-to-peer network with no central command. Highly resilient to disruption "
        "but difficult to coordinate large-scale operations."
    ),
    CellStructure.HUB_AND_SPOKE: (
        "Central coordination hub linked to semi-autonomous operational cells. "
        "Balances coordination with resilience; hub node is the critical vulnerability."
    ),
    CellStructure.CHAIN: (
        "Linear cell-to-cell link — each cell knows only its upstream and downstream neighbors. "
        "Maximum operational security but slow information flow."
    ),
    CellStructure.HYBRID: (
        "Combines multiple structures across the network, adapting to operational context. "
        "Most resilient; requires holistic network analysis to map."
    ),
}
