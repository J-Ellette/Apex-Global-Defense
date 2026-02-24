from __future__ import annotations

from app.models import AttackCategory, AttackTypeEntry

# ---------------------------------------------------------------------------
# Terror Attack Type Catalog
# ---------------------------------------------------------------------------

ATTACK_TYPE_CATALOG: list[AttackTypeEntry] = [
    AttackTypeEntry(
        id="VRAM",
        category=AttackCategory.KINETIC,
        label="Vehicle Ramming Attack",
        description=(
            "Use of a vehicle (car, truck, or bus) as a weapon to deliberately drive "
            "into crowds or groups of people. Requires minimal planning and no specialist skills. "
            "Highly effective in pedestrian-dense areas."
        ),
        typical_perpetrators=["Lone wolf", "Small cell", "Inspired attacker"],
        typical_targets=["Pedestrian zone", "Market", "Stadium", "Transport hub", "Parade route"],
        avg_killed_low=2,
        avg_killed_high=15,
        avg_wounded_low=10,
        avg_wounded_high=80,
        detection_window="Minutes to hours (vehicle acquisition observable)",
        countermeasures=[
            "Vehicle barriers / bollards",
            "Traffic restriction in high-density areas",
            "Perimeter standoff distance",
            "CCTV monitoring of access routes",
            "Emergency vehicle exclusion zones",
        ],
        threat_indicator="Stolen or rented large vehicle near event; individual acting erratically near vehicle access",
        color_hex="#DC2626",
    ),
    AttackTypeEntry(
        id="ASHT",
        category=AttackCategory.KINETIC,
        label="Active Shooter / Gunman Attack",
        description=(
            "Armed individual(s) conducting indiscriminate or targeted shooting at a location. "
            "Often motivated by ideology, personal grievance, or directed by a terror group. "
            "High lethality in enclosed spaces with limited egress."
        ),
        typical_perpetrators=["Lone wolf", "Directed cell", "Grievance-motivated individual"],
        typical_targets=["School", "House of worship", "Concert venue", "Market", "Government building"],
        avg_killed_low=3,
        avg_killed_high=25,
        avg_wounded_low=5,
        avg_wounded_high=60,
        detection_window="Seconds to minutes (gunshots audible)",
        countermeasures=[
            "Armed security / law enforcement on site",
            "Run-Hide-Fight training for staff",
            "Panic button / silent alarm systems",
            "Hardened entry points and lockdown capability",
            "Real-time communication with law enforcement",
        ],
        threat_indicator="Unusual interest in security arrangements; test visits; online radicalization signals",
        color_hex="#B91C1C",
    ),
    AttackTypeEntry(
        id="SBOM",
        category=AttackCategory.EXPLOSIVE,
        label="Suicide Bombing (PBIED)",
        description=(
            "Attacker wearing or carrying an explosive device detonates in a crowded area. "
            "Combines the lethality of an explosive with the mobility of a human operator. "
            "Often used in soft-target environments with high crowd density."
        ),
        typical_perpetrators=["Ideologically motivated individual", "Terror cell operative"],
        typical_targets=["Market", "Transport hub", "House of worship", "Stadium", "Hotel"],
        avg_killed_low=5,
        avg_killed_high=40,
        avg_wounded_low=20,
        avg_wounded_high=150,
        detection_window="Minutes to hours (behavioral indicators observable)",
        countermeasures=[
            "Explosive trace detection at entry points",
            "Behavioral detection officers",
            "Standoff screening with K9 units",
            "Blast-mitigating furniture and architecture",
            "Mandatory bag screening",
        ],
        threat_indicator="Individual wearing bulky clothing in warm weather; avoids eye contact; excessive sweating; hands in pocket",
        color_hex="#F97316",
    ),
    AttackTypeEntry(
        id="HSTG",
        category=AttackCategory.KINETIC,
        label="Hostage Taking / Siege",
        description=(
            "Seizure of individuals or a facility to use as leverage for political demands, "
            "prisoner release, or ransom. Can involve extended standoffs requiring specialized "
            "response teams and negotiation capability."
        ),
        typical_perpetrators=["Organized cell", "Criminal-terrorist hybrid group"],
        typical_targets=["Embassy", "Hotel", "School", "Government building", "Financial center"],
        avg_killed_low=1,
        avg_killed_high=20,
        avg_wounded_low=2,
        avg_wounded_high=30,
        detection_window="Minutes (visible takeover); hours (covert infiltration)",
        countermeasures=[
            "Access control and mantrap entry systems",
            "Safe rooms and secure communications",
            "Crisis negotiation team on standby",
            "Counter-terrorism rapid response unit",
            "Hardened communications infrastructure",
        ],
        threat_indicator="Reconnaissance visits; unusual inquiries about building layout; pro-organization graffiti nearby",
        color_hex="#7C3AED",
    ),
    AttackTypeEntry(
        id="EXPL",
        category=AttackCategory.EXPLOSIVE,
        label="Planted Explosive Device",
        description=(
            "Improvised or manufactured explosive device concealed in a vehicle, bag, or "
            "infrastructure and detonated remotely, by timer, or by victim operation. "
            "Used to maximize casualties or disrupt critical infrastructure."
        ),
        typical_perpetrators=["Terror cell", "State-sponsored actor", "Separatist group"],
        typical_targets=["Transport hub", "Government building", "Financial center", "Market", "Stadium"],
        avg_killed_low=3,
        avg_killed_high=30,
        avg_wounded_low=15,
        avg_wounded_high=200,
        detection_window="Hours to days (device placement observable via CCTV)",
        countermeasures=[
            "Regular security sweeps and vehicle checks",
            "Suspicious package reporting and public awareness",
            "Explosive detection dogs",
            "Mail screening and delivery control",
            "Bomb disposal unit pre-deployment at major events",
        ],
        threat_indicator="Unattended bag or package; unusual parked vehicle; electronic components or wiring visible",
        color_hex="#D97706",
    ),
    AttackTypeEntry(
        id="CHEM",
        category=AttackCategory.CHEMICAL_BIO,
        label="Chemical Agent Attack",
        description=(
            "Release of toxic chemical agents (nerve agents, choking agents, blister agents) "
            "in a populated area via aerosol, explosive dispersal, or contamination of "
            "food/water supply. Even small quantities can cause mass casualties."
        ),
        typical_perpetrators=["State-sponsored actor", "Well-funded terror organization", "Sophisticated cell"],
        typical_targets=["Transport hub", "Stadium", "Government building", "Water supply", "Ventilation system"],
        avg_killed_low=5,
        avg_killed_high=500,
        avg_wounded_low=50,
        avg_wounded_high=2000,
        detection_window="Seconds (onset of symptoms) to hours (covert dispersal)",
        countermeasures=[
            "CBRN detection sensors at key entry points",
            "Sealed HVAC systems with air filtration",
            "Rapid medical antidote stockpiles",
            "Mass casualty decontamination capability",
            "CBRN-trained first responders on site",
        ],
        threat_indicator="Unusual odor; multiple individuals collapsing simultaneously; unexplained liquid or powder near ventilation",
        color_hex="#059669",
    ),
    AttackTypeEntry(
        id="BIOL",
        category=AttackCategory.CHEMICAL_BIO,
        label="Biological / Bioterrorism Attack",
        description=(
            "Deliberate release of pathogens (anthrax, smallpox, plague) or biological toxins "
            "into a population. Effects may be delayed by days or weeks, complicating attribution "
            "and enabling wide geographic spread before detection."
        ),
        typical_perpetrators=["State-sponsored actor", "Sophisticated terror organization", "Lone scientist"],
        typical_targets=["Water supply", "Food processing", "Hospital", "Transport hub", "Government building"],
        avg_killed_low=10,
        avg_killed_high=1000,
        avg_wounded_low=100,
        avg_wounded_high=10000,
        detection_window="Days to weeks (incubation period masks initial attack)",
        countermeasures=[
            "BioWatch detection sensors in public spaces",
            "Syndromic surveillance and early warning systems",
            "Strategic national stockpile of vaccines/antibiotics",
            "Laboratory surge capacity for rapid diagnosis",
            "Quarantine and containment protocols",
        ],
        threat_indicator="Unusual disease cluster; atypical symptoms in multiple patients; missing cultures from laboratory",
        color_hex="#10B981",
    ),
    AttackTypeEntry(
        id="CYBR",
        category=AttackCategory.CYBER,
        label="Cyber / Infrastructure Disruption",
        description=(
            "Targeted cyberattack against critical infrastructure (power grids, water treatment, "
            "financial systems, emergency services) to create physical harm, panic, or economic "
            "disruption. Often used in conjunction with kinetic attacks."
        ),
        typical_perpetrators=["State-sponsored APT", "Hacktivist group", "Ransomware criminal"],
        typical_targets=["Critical infrastructure", "Financial center", "Hospital", "Government building", "Transport hub"],
        avg_killed_low=0,
        avg_killed_high=50,
        avg_wounded_low=0,
        avg_wounded_high=1000,
        detection_window="Hours to days (anomaly detection dependent on monitoring maturity)",
        countermeasures=[
            "Network segmentation and air-gapping critical systems",
            "Real-time intrusion detection and SOC monitoring",
            "Offline backup and manual fallback procedures",
            "Regular penetration testing and red team exercises",
            "Multi-factor authentication and zero-trust architecture",
        ],
        threat_indicator="Unusual network traffic; repeated failed authentication; insider threat behavior; dark web chatter",
        color_hex="#2563EB",
    ),
    AttackTypeEntry(
        id="ASSN",
        category=AttackCategory.KINETIC,
        label="Assassination / Targeted Killing",
        description=(
            "Planned killing of a specific high-value individual — political leader, "
            "military commander, intelligence officer, or cultural figure — for political "
            "or ideological objectives. Often preceded by extensive surveillance."
        ),
        typical_perpetrators=["State-sponsored assassin", "Terror cell", "Hired operative"],
        typical_targets=["Government building", "Hotel", "Transport hub", "Embassy", "Military base"],
        avg_killed_low=1,
        avg_killed_high=5,
        avg_wounded_low=0,
        avg_wounded_high=10,
        detection_window="Days to weeks (surveillance phase observable)",
        countermeasures=[
            "Protective security detail (PSD) for high-risk individuals",
            "Countersurveillance and route variation",
            "Threat intelligence monitoring",
            "Vehicle security and route security assessment",
            "Emergency medical response planning",
        ],
        threat_indicator="Unknown individuals photographing routes or residences; suspicious vehicle follows; threat communications",
        color_hex="#6B7280",
    ),
    AttackTypeEntry(
        id="INFR",
        category=AttackCategory.HYBRID,
        label="Critical Infrastructure Attack",
        description=(
            "Physical or cyber-physical attack on power grids, pipelines, water treatment, "
            "transportation networks, or communications infrastructure. Designed to create "
            "cascading societal disruption beyond the immediate target."
        ),
        typical_perpetrators=["State-sponsored actor", "Well-organized terror group", "Saboteur"],
        typical_targets=["Critical infrastructure", "Transport hub", "Financial center", "Government building"],
        avg_killed_low=0,
        avg_killed_high=20,
        avg_wounded_low=0,
        avg_wounded_high=100,
        detection_window="Hours to days (system monitoring dependent)",
        countermeasures=[
            "Physical perimeter security around critical assets",
            "Redundant systems and failover capability",
            "SCADA / ICS monitoring and anomaly detection",
            "Workforce vetting and insider threat program",
            "Regular infrastructure resilience exercises",
        ],
        threat_indicator="Unusual activity near pipeline or substation; drone overflights; insider unusual access patterns",
        color_hex="#0891B2",
    ),
]

ATTACK_TYPE_MAP: dict[str, AttackTypeEntry] = {e.id: e for e in ATTACK_TYPE_CATALOG}
