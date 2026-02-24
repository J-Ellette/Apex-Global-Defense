from __future__ import annotations

"""
CBRN Agent Catalog — representative Chemical, Biological, Radiological, and
Nuclear (CBRN) threat agents with key dispersion / casualty parameters.

All threshold values are illustrative / open-source references only (e.g.,
NIOSH IDLH, NATO planning figures, published open-source casualty doctrine).
They are NOT classified and are included solely for simulation / planning
purposes.
"""

from app.models import CBRNAgent

AGENT_CATALOG: list[CBRNAgent] = [
    # ── Chemical ────────────────────────────────────────────────────────────
    CBRNAgent(
        id="VX",
        name="VX (Nerve Agent)",
        category="CHEMICAL",
        sub_category="Nerve Agent",
        description=(
            "Persistent organophosphate nerve agent. Inhibits acetylcholinesterase, "
            "causing continuous nerve stimulation. Lethal in very small doses through "
            "skin absorption or inhalation."
        ),
        state="LIQUID",
        persistency="HIGH",
        vapor_pressure_pa=0.0007,
        density_kg_m3=1.008,
        molecular_weight=267.37,
        # mg·min/m³ inhalation LCt50 (estimated)
        lct50_mg_min_m3=10.0,
        # mg·min/m³ incapacitating Ct50
        ict50_mg_min_m3=2.0,
        # IDLH mg/m³
        idlh_mg_m3=0.00003,
        half_life_min=None,
        protective_action="Full MOPP-4; decon required",
        nato_code="VX",
        color_hex="#8B0000",
    ),
    CBRNAgent(
        id="GB",
        name="Sarin (GB)",
        category="CHEMICAL",
        sub_category="Nerve Agent",
        description=(
            "Volatile nerve agent. Non-persistent. Rapid incapacitation through "
            "inhalation or skin contact. Causes miosis, seizures, respiratory failure."
        ),
        state="VAPOR",
        persistency="LOW",
        vapor_pressure_pa=2130.0,
        density_kg_m3=1.0887,
        molecular_weight=140.09,
        lct50_mg_min_m3=35.0,
        ict50_mg_min_m3=5.0,
        idlh_mg_m3=0.00003,
        half_life_min=None,
        protective_action="MOPP-4; area clears within hours",
        nato_code="GB",
        color_hex="#FF4500",
    ),
    CBRNAgent(
        id="HD",
        name="Mustard Gas (HD)",
        category="CHEMICAL",
        sub_category="Blister Agent",
        description=(
            "Persistent vesicant (blister agent). Causes delayed skin, eye, and "
            "respiratory tract injuries. Low vapor pressure makes it a persistent "
            "ground hazard."
        ),
        state="LIQUID",
        persistency="HIGH",
        vapor_pressure_pa=14.5,
        density_kg_m3=1.27,
        molecular_weight=159.08,
        lct50_mg_min_m3=1500.0,
        ict50_mg_min_m3=200.0,
        idlh_mg_m3=0.003,
        half_life_min=None,
        protective_action="MOPP-4; area decontamination required",
        nato_code="HD",
        color_hex="#DAA520",
    ),
    CBRNAgent(
        id="CL2",
        name="Chlorine (CL)",
        category="CHEMICAL",
        sub_category="Choking Agent",
        description=(
            "Greenish-yellow gas with pungent odor. Industrial chemical used as a "
            "weapon in WWI. Causes pulmonary edema at high concentrations."
        ),
        state="GAS",
        persistency="LOW",
        vapor_pressure_pa=676000.0,
        density_kg_m3=3.21,
        molecular_weight=70.9,
        lct50_mg_min_m3=19000.0,
        ict50_mg_min_m3=1800.0,
        idlh_mg_m3=29.0,
        half_life_min=None,
        protective_action="Self-contained breathing apparatus (SCBA); evacuate downwind",
        nato_code="CL",
        color_hex="#ADFF2F",
    ),
    CBRNAgent(
        id="AC",
        name="Hydrogen Cyanide (AC)",
        category="CHEMICAL",
        sub_category="Blood Agent",
        description=(
            "Rapidly acting blood agent. Prevents cellular respiration by binding "
            "cytochrome oxidase. High vapor pressure; non-persistent in open areas."
        ),
        state="GAS",
        persistency="LOW",
        vapor_pressure_pa=98700.0,
        density_kg_m3=0.688,
        molecular_weight=27.03,
        lct50_mg_min_m3=2500.0,
        ict50_mg_min_m3=200.0,
        idlh_mg_m3=50.0,
        half_life_min=None,
        protective_action="SCBA or MOPP-4; area ventilates quickly",
        nato_code="AC",
        color_hex="#FF69B4",
    ),
    # ── Biological ──────────────────────────────────────────────────────────
    CBRNAgent(
        id="BA",
        name="Anthrax (Bacillus anthracis)",
        category="BIOLOGICAL",
        sub_category="Bacterial Spore",
        description=(
            "Spore-forming bacterium. Inhalation anthrax has high lethality if "
            "untreated. Spores are highly persistent in the environment (decades)."
        ),
        state="AEROSOL",
        persistency="VERY_HIGH",
        vapor_pressure_pa=None,
        density_kg_m3=None,
        molecular_weight=None,
        lct50_mg_min_m3=None,
        ict50_mg_min_m3=None,
        idlh_mg_m3=None,
        # Infectious dose ~ 8,000–10,000 spores (inhaled); ID50 ≈ 2,500–55,000 spores
        id50_particles=8000.0,
        half_life_min=None,
        protective_action="MOPP-4; prophylactic antibiotics; decontaminate with bleach",
        nato_code="BA",
        color_hex="#556B2F",
    ),
    CBRNAgent(
        id="BX",
        name="Botulinum Toxin (Type A)",
        category="BIOLOGICAL",
        sub_category="Bacterial Toxin",
        description=(
            "Most potent known toxin. Inhalation or ingestion causes flaccid paralysis "
            "and respiratory failure. Non-contagious."
        ),
        state="AEROSOL",
        persistency="MEDIUM",
        vapor_pressure_pa=None,
        density_kg_m3=None,
        molecular_weight=None,
        lct50_mg_min_m3=0.000028,
        ict50_mg_min_m3=0.000002,
        idlh_mg_m3=None,
        half_life_min=None,
        protective_action="MOPP-4; antitoxin if available; supportive care",
        nato_code="BX",
        color_hex="#8B4513",
    ),
    CBRNAgent(
        id="YP",
        name="Plague (Yersinia pestis)",
        category="BIOLOGICAL",
        sub_category="Bacterial",
        description=(
            "Causative agent of bubonic and pneumonic plague. Pneumonic form is "
            "highly contagious via aerosol. High lethality if untreated."
        ),
        state="AEROSOL",
        persistency="LOW",
        vapor_pressure_pa=None,
        density_kg_m3=None,
        molecular_weight=None,
        lct50_mg_min_m3=None,
        ict50_mg_min_m3=None,
        id50_particles=100.0,
        half_life_min=60.0,
        protective_action="N95+ respirator; prophylactic antibiotics; isolation of cases",
        nato_code="YP",
        color_hex="#DC143C",
    ),
    # ── Radiological ────────────────────────────────────────────────────────
    CBRNAgent(
        id="CS137",
        name="Cesium-137 (Dirty Bomb)",
        category="RADIOLOGICAL",
        sub_category="Gamma Emitter",
        description=(
            "Common dirty bomb isotope. Gamma emitter with 30-year half-life. "
            "Contamination creates long-term area denial. Causes radiation sickness "
            "at high doses."
        ),
        state="PARTICULATE",
        persistency="VERY_HIGH",
        vapor_pressure_pa=None,
        density_kg_m3=None,
        molecular_weight=136.91,
        lct50_mg_min_m3=None,
        ict50_mg_min_m3=None,
        # Dose-based thresholds (Gy)
        lethal_dose_gy=4.5,
        incapacitating_dose_gy=1.0,
        half_life_min=None,
        protective_action="Evacuate; seal buildings; monitor with dosimetry; avoid inhalation of dust",
        nato_code="RAD-CS137",
        color_hex="#FFD700",
    ),
    CBRNAgent(
        id="CO60",
        name="Cobalt-60",
        category="RADIOLOGICAL",
        sub_category="Gamma Emitter",
        description=(
            "High-energy gamma emitter used in medical/industrial devices. Very "
            "dangerous if dispersed. Half-life ~5.27 years."
        ),
        state="PARTICULATE",
        persistency="HIGH",
        vapor_pressure_pa=None,
        density_kg_m3=None,
        molecular_weight=59.93,
        lct50_mg_min_m3=None,
        ict50_mg_min_m3=None,
        lethal_dose_gy=4.5,
        incapacitating_dose_gy=1.0,
        half_life_min=None,
        protective_action="Distance; shielding (lead/concrete); dosimetry monitoring",
        nato_code="RAD-CO60",
        color_hex="#FFA500",
    ),
    # ── Nuclear ─────────────────────────────────────────────────────────────
    CBRNAgent(
        id="IND-10KT",
        name="IND 10 kT (Improvised Nuclear Device)",
        category="NUCLEAR",
        sub_category="Fission Device",
        description=(
            "10-kiloton improvised nuclear device. Produces blast, thermal, and "
            "radiation effects. Fallout zone extends tens of kilometers downwind."
        ),
        state="EXPLOSION",
        persistency="HIGH",
        vapor_pressure_pa=None,
        density_kg_m3=None,
        molecular_weight=None,
        lct50_mg_min_m3=None,
        ict50_mg_min_m3=None,
        yield_kt=10.0,
        lethal_dose_gy=4.5,
        incapacitating_dose_gy=1.0,
        half_life_min=None,
        protective_action="Evacuate 10+ km immediately; shelter-in-place at 10–30 km; decontaminate",
        nato_code="NUC-10KT",
        color_hex="#FF0000",
    ),
    CBRNAgent(
        id="IND-100KT",
        name="IND 100 kT",
        category="NUCLEAR",
        sub_category="Fission Device",
        description=(
            "100-kiloton nuclear device. Severe blast, thermal, and radiation effects "
            "over a wide area. Fallout extends 100+ km downwind under typical conditions."
        ),
        state="EXPLOSION",
        persistency="HIGH",
        vapor_pressure_pa=None,
        density_kg_m3=None,
        molecular_weight=None,
        lct50_mg_min_m3=None,
        ict50_mg_min_m3=None,
        yield_kt=100.0,
        lethal_dose_gy=4.5,
        incapacitating_dose_gy=1.0,
        half_life_min=None,
        protective_action="Evacuate 30+ km immediately; shelter-in-place up to 80 km",
        nato_code="NUC-100KT",
        color_hex="#8B0000",
    ),
]

AGENT_MAP: dict[str, CBRNAgent] = {a.id: a for a in AGENT_CATALOG}
