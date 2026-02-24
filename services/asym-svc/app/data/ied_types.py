from __future__ import annotations

from app.models import IEDCategory, IEDTypeEntry

# ---------------------------------------------------------------------------
# IED Type Catalog
# ---------------------------------------------------------------------------

IED_TYPE_CATALOG: list[IEDTypeEntry] = [
    IEDTypeEntry(
        id="VBIED",
        category=IEDCategory.VEHICLE,
        label="Vehicle-Borne IED (VBIED)",
        description=(
            "Large explosive device concealed in a vehicle. Capable of mass-casualty attacks "
            "against buildings, checkpoints, and large gatherings."
        ),
        typical_yield_kg_tnt_equiv=50.0,
        lethal_radius_m=30.0,
        injury_radius_m=100.0,
        blast_radius_m=200.0,
        avg_killed=15,
        avg_wounded=60,
        detection_difficulty="MEDIUM",
        primary_effect="BLAST",
        countermeasures=[
            "Vehicle checkpoints with standoff distance",
            "Vehicle-borne explosive trace detection",
            "Bollards and anti-ram barriers",
            "CCTV and pattern-of-life analysis",
        ],
        construction_complexity="HIGH",
        color_hex="#EF4444",
    ),
    IEDTypeEntry(
        id="SVBIED",
        category=IEDCategory.VEHICLE,
        label="Suicide VBIED (SVBIED)",
        description=(
            "Driver-operated vehicle bomb with a suicide operator to bypass vehicle checkpoints "
            "and maximize placement accuracy. Extremely high casualty potential."
        ),
        typical_yield_kg_tnt_equiv=100.0,
        lethal_radius_m=50.0,
        injury_radius_m=150.0,
        blast_radius_m=300.0,
        avg_killed=30,
        avg_wounded=100,
        detection_difficulty="HIGH",
        primary_effect="BLAST",
        countermeasures=[
            "Perimeter security with standoff",
            "Traffic management and slowing barriers",
            "Behavioral detection at checkpoints",
            "Armed response assets",
        ],
        construction_complexity="HIGH",
        color_hex="#B91C1C",
    ),
    IEDTypeEntry(
        id="PBIED",
        category=IEDCategory.PERSON_BORNE,
        label="Person-Borne IED (PBIED / Suicide Vest)",
        description=(
            "Explosive device worn on or carried by a person. Used in close-quarters attacks "
            "against crowds, checkpoints, and personnel."
        ),
        typical_yield_kg_tnt_equiv=5.0,
        lethal_radius_m=5.0,
        injury_radius_m=20.0,
        blast_radius_m=50.0,
        avg_killed=8,
        avg_wounded=30,
        detection_difficulty="HIGH",
        primary_effect="BLAST_FRAGMENTATION",
        countermeasures=[
            "Screening portals and metal detectors",
            "Behavioral analysis and profiling",
            "Standoff distance policies",
            "K9 explosive detection",
        ],
        construction_complexity="MEDIUM",
        color_hex="#DC2626",
    ),
    IEDTypeEntry(
        id="PLACED_IED",
        category=IEDCategory.PLACED,
        label="Placed / Roadside IED",
        description=(
            "Emplaced device triggered by command wire, pressure plate, infrared, or remote control. "
            "Primary anti-vehicle and anti-personnel weapon in asymmetric campaigns."
        ),
        typical_yield_kg_tnt_equiv=8.0,
        lethal_radius_m=8.0,
        injury_radius_m=25.0,
        blast_radius_m=60.0,
        avg_killed=3,
        avg_wounded=10,
        detection_difficulty="MEDIUM",
        primary_effect="BLAST_FRAGMENTATION",
        countermeasures=[
            "Route clearance patrols and EOD",
            "Ground-penetrating radar",
            "Mine rollers and vehicle armor",
            "Pattern-of-life and intelligence analysis",
        ],
        construction_complexity="LOW",
        color_hex="#F97316",
    ),
    IEDTypeEntry(
        id="EFP",
        category=IEDCategory.EXPLOSIVELY_FORMED,
        label="Explosively Formed Penetrator (EFP)",
        description=(
            "Shaped charge using a metal plate to form a high-velocity penetrator. "
            "Designed to defeat armored vehicles. Iranian-developed technology widely proliferated."
        ),
        typical_yield_kg_tnt_equiv=2.0,
        lethal_radius_m=3.0,
        injury_radius_m=10.0,
        blast_radius_m=30.0,
        avg_killed=2,
        avg_wounded=4,
        detection_difficulty="HIGH",
        primary_effect="ARMOR_PENETRATION",
        countermeasures=[
            "Standoff distance and route variation",
            "Reactive armor and Trophy APS",
            "Signal jamming (for remote-detonated variants)",
            "Pattern-of-life and intelligence on emplacers",
        ],
        construction_complexity="HIGH",
        color_hex="#7C3AED",
    ),
    IEDTypeEntry(
        id="COMMAND_WIRE",
        category=IEDCategory.PLACED,
        label="Command Wire IED",
        description=(
            "Placed device detonated via a physical electrical wire by an observer. "
            "Reliable ignition, but the wire creates a traceable physical signature."
        ),
        typical_yield_kg_tnt_equiv=10.0,
        lethal_radius_m=10.0,
        injury_radius_m=30.0,
        blast_radius_m=70.0,
        avg_killed=4,
        avg_wounded=12,
        detection_difficulty="LOW",
        primary_effect="BLAST_FRAGMENTATION",
        countermeasures=[
            "Route clearance and wire detection",
            "Aerial surveillance of approaches",
            "EOD counter-IED teams",
        ],
        construction_complexity="LOW",
        color_hex="#EA580C",
    ),
    IEDTypeEntry(
        id="RCIED",
        category=IEDCategory.REMOTE_CONTROLLED,
        label="Remote-Controlled IED (RCIED)",
        description=(
            "Device detonated by radio frequency, cellular, or satellite signal. "
            "Allows emplacement and remote detonation from safe distance."
        ),
        typical_yield_kg_tnt_equiv=10.0,
        lethal_radius_m=10.0,
        injury_radius_m=30.0,
        blast_radius_m=70.0,
        avg_killed=4,
        avg_wounded=12,
        detection_difficulty="MEDIUM",
        primary_effect="BLAST_FRAGMENTATION",
        countermeasures=[
            "Electronic countermeasure (ECM) jammers",
            "RF detection equipment",
            "Signal intelligence on detonator frequencies",
        ],
        construction_complexity="MEDIUM",
        color_hex="#D97706",
    ),
    IEDTypeEntry(
        id="PRESSURE_PLATE",
        category=IEDCategory.VICTIM_OPERATED,
        label="Pressure-Plate IED (PPIED)",
        description=(
            "Victim-operated device triggered by weight. Does not require an operator "
            "on-site after emplacement, making counter-surveillance more difficult."
        ),
        typical_yield_kg_tnt_equiv=6.0,
        lethal_radius_m=6.0,
        injury_radius_m=20.0,
        blast_radius_m=50.0,
        avg_killed=2,
        avg_wounded=8,
        detection_difficulty="HIGH",
        primary_effect="BLAST_FRAGMENTATION",
        countermeasures=[
            "Metal detectors and ground-penetrating radar",
            "Route clearance by dismounted EOD",
            "Mine-protected vehicles",
        ],
        construction_complexity="LOW",
        color_hex="#CA8A04",
    ),
    IEDTypeEntry(
        id="DRONE_IED",
        category=IEDCategory.AERIAL,
        label="Drone-Delivered IED",
        description=(
            "Commercial or military-grade UAV modified to drop or deliver a small explosive payload. "
            "Emerging threat with increasing proliferation and sophistication."
        ),
        typical_yield_kg_tnt_equiv=0.5,
        lethal_radius_m=3.0,
        injury_radius_m=8.0,
        blast_radius_m=20.0,
        avg_killed=1,
        avg_wounded=4,
        detection_difficulty="HIGH",
        primary_effect="BLAST_FRAGMENTATION",
        countermeasures=[
            "Counter-UAS (C-UAS) electronic systems",
            "RF jamming and drone detection radar",
            "Physical netting and hardened positions",
            "Pattern-of-life on drone activity",
        ],
        construction_complexity="MEDIUM",
        color_hex="#2563EB",
    ),
]

IED_TYPE_MAP: dict[str, IEDTypeEntry] = {e.id: e for e in IED_TYPE_CATALOG}
