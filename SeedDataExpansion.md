# AGD Seed Data Expansion Plan

## Overview

This document defines the expansion targets for three seed data domains:

1. **Economic Warfare** — sanctions, trade routes, economic indicators (from 5 → 30+ nations)
2. **Information Operations** — narratives, campaigns, indicators (from 2 → 10+ state actors)
3. **Equipment Catalog** — real-world military equipment specs (new, 270–450 entries)

All data is **UNCLASSIFIED / open-source**. No schema changes are required — all expansions use existing table structures.

---

## 1. Economic Warfare Seed Expansion

### Current State

- **`012_econ_schema.sql`** seeds 5 sanctioned nations: Russia, Iran, North Korea, Belarus, Venezuela
- 5 trade routes, 10 economic indicators
- 8 sanction types supported: `ASSET_FREEZE`, `TRADE_EMBARGO`, `FINANCIAL_CUTOFF`, `SECTORAL`, `ARMS_EMBARGO`, `TRAVEL_BAN`, `DIPLOMATIC`, `TECHNOLOGY_BAN`

### Expansion Target: 20+ Additional Sanctioned Nations

#### Comprehensive Sanctions (near-total trade/financial bans)

| Country | Code | Sanction Type | Imposing Parties | Effective Date | GDP Impact % | Notes |
|---------|------|---------------|------------------|----------------|-------------|-------|
| Cuba | CUB | TRADE_EMBARGO | USA | 1962-02-07 | 5.0 | Full US embargo since 1962; limited humanitarian exceptions |
| Syria | SYR | TRADE_EMBARGO | USA, EU | 2011-08-18 | 8.5 | Broad restrictions on energy, finance, investment; partial EU/UK easing in 2025 for humanitarian purposes |

#### Regional/Sectoral Sanctions

| Country | Code | Sanction Type | Imposing Parties | Effective Date | GDP Impact % | Notes |
|---------|------|---------------|------------------|----------------|-------------|-------|
| Myanmar (Burma) | MMR | SECTORAL | USA, EU, UK | 2021-02-01 | 3.2 | Post-coup military regime; energy, mining, financial sector restrictions |
| Crimea (occupied) | UKR | TRADE_EMBARGO | USA, EU | 2014-03-17 | N/A | Full embargo on business and investment in occupied Crimea, Donetsk, Luhansk |

#### Targeted/SDN-List Sanctions

| Country | Code | Sanction Type | Imposing Parties | Effective Date | GDP Impact % | Notes |
|---------|------|---------------|------------------|----------------|-------------|-------|
| Sudan | SDN | ASSET_FREEZE | USA, EU, UN | 1997-11-03 | 2.8 | Targeted sanctions on military officials and entities |
| South Sudan | SSD | ARMS_EMBARGO | UN | 2018-07-13 | 1.5 | UN arms embargo; targeted asset freezes on officials |
| Somalia | SOM | ARMS_EMBARGO | UN | 1992-01-23 | 1.0 | Long-standing UN arms embargo; Al-Shabaab targeted |
| Libya | LBY | ARMS_EMBARGO | UN, EU | 2011-02-26 | 3.5 | UN arms embargo + asset freezes; oil sector restrictions |
| Yemen | YEM | ASSET_FREEZE | USA, UN | 2014-11-07 | 2.0 | Houthi-targeted sanctions; humanitarian exemptions |
| Zimbabwe | ZWE | TRAVEL_BAN | USA, EU | 2003-02-18 | 1.8 | Targeted sanctions on officials; diamond/mining restrictions |
| Central African Republic | CAF | ARMS_EMBARGO | UN | 2013-12-05 | 0.8 | UN arms embargo + travel ban on armed group leaders |
| DR Congo | COD | ARMS_EMBARGO | UN, EU | 2003-07-28 | 1.2 | UN arms embargo; targeted sanctions on armed groups |
| Ethiopia | ETH | ASSET_FREEZE | USA | 2021-09-17 | 1.0 | Targeted post-Tigray conflict sanctions |
| Nicaragua | NIC | ASSET_FREEZE | USA, EU, Canada | 2018-11-27 | 1.5 | Targeted regime sanctions on Ortega government officials |
| Mali | MLI | SECTORAL | EU | 2022-01-10 | 1.8 | EU sanctions on military junta; ECOWAS restrictions |
| Lebanon | LBN | ASSET_FREEZE | USA | 2007-08-01 | 0.5 | Hezbollah-targeted sanctions; financial sector restrictions |
| Afghanistan | AFG | ASSET_FREEZE | USA, UN | 2021-08-15 | 4.0 | Taliban government asset freezes; central bank reserves frozen |
| Iraq | IRQ | SECTORAL | UN (residual) | 2003-05-22 | 0.3 | Residual WMD-related sanctions; largely lifted |
| Eritrea | ERI | ARMS_EMBARGO | UN (lifted 2018) | 2009-12-23 | 1.0 | UN arms embargo (lifted 2018); US targeted sanctions remain |

### Expanded Trade Routes

| Origin | Destination | Commodity | Annual Value USD | Dependency | Disrupted | Disruption Cause |
|--------|-------------|-----------|-----------------|------------|-----------|-----------------|
| CHN | USA | semiconductors | 500,000,000,000 | CRITICAL | No | — |
| RUS | EUR | natural_gas | 85,000,000,000 | CRITICAL | Yes | Russia-Ukraine conflict; Nord Stream sabotage; EU diversification |
| SAU | USA | crude_oil | 140,000,000,000 | HIGH | No | — |
| CHN | EUR | manufactured_goods | 380,000,000,000 | HIGH | No | — |
| USA | CHN | agricultural_products | 26,000,000,000 | MEDIUM | No | — |
| CUB | EUR | sugar_tobacco | 800,000,000 | MEDIUM | Yes | US embargo restricts re-export; limited EU trade |
| SYR | TUR | crude_oil | 2,000,000,000 | HIGH | Yes | Civil war; sanctions; pipeline disruption |
| MMR | CHN | natural_gas | 3,500,000,000 | HIGH | No | — |
| MMR | CHN | jade_gemstones | 15,000,000,000 | CRITICAL | No | Largely unregulated; funds military regime |
| IRN | CHN | crude_oil | 25,000,000,000 | CRITICAL | No | Sanctions evasion via ship-to-ship transfers |
| IRN | IND | crude_oil | 12,000,000,000 | HIGH | Yes | US secondary sanctions pressure |
| RUS | IND | crude_oil | 45,000,000,000 | HIGH | No | Discounted oil trade post-2022 |
| RUS | CHN | crude_oil | 60,000,000,000 | HIGH | No | Power of Siberia pipeline + seaborne |
| UKR | EUR | grain_cereals | 12,000,000,000 | HIGH | Yes | Black Sea blockade; grain corridor negotiations |
| LBY | EUR | crude_oil | 20,000,000,000 | MEDIUM | Yes | Civil conflict; production disruptions |
| SDN | ARE | gold | 4,500,000,000 | HIGH | Yes | Civil war; smuggling networks |
| AFG | PAK | coal_minerals | 1,400,000,000 | MEDIUM | No | Taliban-controlled exports |
| PRK | CHN | coal_iron_ore | 2,000,000,000 | CRITICAL | Yes | UN sanctions; smuggling persists |
| VEN | CHN | crude_oil | 5,000,000,000 | HIGH | Yes | US sanctions; discounted sales |
| COD | CHN | cobalt_coltan | 8,000,000,000 | CRITICAL | No | 70% of world cobalt supply |

### Expanded Economic Indicators

Source data from IMF World Economic Outlook, World Bank, national statistics bureaus.

| Country | Code | GDP Growth % | Inflation % | Unemployment % | Source | Year |
|---------|------|-------------|-------------|----------------|--------|------|
| Russia | RUS | -2.10 | 7.40 | 3.90 | IMF | 2023 |
| Iran | IRN | 1.40 | 44.60 | — | IMF | 2023 |
| North Korea | PRK | -4.50 | — | — | Bank of Korea | 2022 |
| China | CHN | 5.20 | 0.20 | — | NBS China | 2023 |
| USA | USA | 2.50 | 3.40 | — | BEA/BLS | 2023 |
| Cuba | CUB | 1.80 | 39.00 | 1.40 | ONEI Cuba / IMF | 2023 |
| Syria | SYR | -3.20 | 115.00 | 50.00 | World Bank est. | 2023 |
| Myanmar | MMR | 2.50 | 14.20 | 2.20 | World Bank | 2023 |
| Sudan | SDN | -12.00 | 256.00 | 28.00 | IMF / World Bank | 2023 |
| Venezuela | VEN | 4.00 | 190.00 | 6.40 | IMF | 2023 |
| Afghanistan | AFG | -6.20 | 10.30 | 14.40 | World Bank | 2023 |
| Libya | LBY | 12.50 | 3.70 | 19.50 | IMF | 2023 |
| Yemen | YEM | -2.00 | 30.00 | 13.50 | World Bank est. | 2023 |
| Zimbabwe | ZWE | 3.50 | 104.70 | 19.30 | IMF | 2023 |
| DR Congo | COD | 6.20 | 19.90 | 4.50 | IMF | 2023 |
| Ethiopia | ETH | 6.10 | 28.70 | 3.50 | IMF | 2023 |
| Nicaragua | NIC | 4.60 | 8.40 | 4.30 | IMF | 2023 |
| Mali | MLI | 4.80 | 2.10 | 7.50 | IMF | 2023 |
| Lebanon | LBN | -0.20 | 221.30 | 29.60 | IMF / World Bank | 2023 |
| Belarus | BLR | 3.90 | 5.00 | 3.60 | IMF | 2023 |
| Somalia | SOM | 2.80 | 6.10 | — | IMF | 2023 |
| South Sudan | SSD | -1.00 | 10.50 | — | World Bank est. | 2023 |
| Eritrea | ERI | 2.90 | 5.60 | — | IMF est. | 2023 |
| CAR | CAF | 1.00 | 3.40 | — | IMF | 2023 |
| Iraq | IRQ | 3.70 | 4.40 | 15.50 | IMF | 2023 |

### Data Sources for Economic Module

| Source | URL | Use |
|--------|-----|-----|
| OFAC Sanctions Programs | https://ofac.treasury.gov/sanctions-programs-and-country-information | Authoritative US sanctions list |
| EU Sanctions Map | https://www.sanctionsmap.eu/ | EU restrictive measures by country |
| UN Sanctions | https://www.un.org/securitycouncil/sanctions/information | UN Security Council sanctions regimes |
| DLA Piper Sanctions Matrix | https://www.dlapiper.com/en-us/insights/publications/global-sanctions-alert/ | Cross-jurisdiction comparison |
| IMF World Economic Outlook | https://www.imf.org/en/Publications/WEO | GDP, inflation, unemployment by country |
| World Bank Open Data | https://data.worldbank.org/ | Trade, development indicators |
| CNAS Sanctions Tracker | https://www.cnas.org/publications/reports/sanctions-by-the-numbers-2024-year-in-review | Annual sanctions analysis |

---

## 2. Information Operations Seed Expansion

### Current State

- **`013_infoops_schema.sql`** seeds 2 state actors: Russia (2 narratives, 1 campaign), China (1 narrative, 1 campaign)
- 3 disinformation indicators, 0 attribution assessments

### Expansion Target: 10+ State Actors

#### New Narrative Threats

| # | Title | Origin | Code | Threat Level | Targets | Platforms | Key Claims |
|---|-------|--------|------|-------------|---------|-----------|------------|
| 4 | Iranian Axis of Resistance Propaganda | Iran | IRN | HIGH | ISR, USA, SAU, ARE, GBR | STATE_MEDIA, SOCIAL_MEDIA, MESSAGING_APP | "Resistance is the only path to liberation"; "US bases are legitimate military targets"; "Normalization with Israel is betrayal of Palestine" |
| 5 | DPRK Nuclear Sovereignty Narrative | North Korea | PRK | MEDIUM | USA, KOR, JPN | STATE_MEDIA, NEWS_OUTLET | "Nuclear deterrent guarantees sovereignty"; "US military exercises are invasion rehearsals"; "Sanctions are acts of war" |
| 6 | Indian Hindu Nationalist Amplification | India | IND | MEDIUM | PAK, BGD, GBR, CAN | SOCIAL_MEDIA, VIDEO_PLATFORM, MESSAGING_APP | "Pakistan is a failed state harboring terrorism"; "Indian Muslims are well-treated"; "Western media is anti-India" |
| 7 | Turkish Neo-Ottoman Regional Narrative | Turkey | TUR | MEDIUM | GRC, SYR, IRQ, FRA, DEU | STATE_MEDIA, SOCIAL_MEDIA, NEWS_OUTLET | "Turkey is the natural leader of the Muslim world"; "Kurdish autonomy threatens regional stability"; "Europe is hostile to Islam" |
| 8 | Saudi Vision 2030 Image Laundering | Saudi Arabia | SAU | LOW | USA, GBR, FRA | SOCIAL_MEDIA, NEWS_OUTLET, VIDEO_PLATFORM | "Saudi Arabia is modernizing rapidly"; "Critics are funded by Qatar/Iran"; "MBS is a reformer" |
| 9 | UAE Democratic Stability Narrative | UAE | ARE | LOW | USA, GBR | SOCIAL_MEDIA, NEWS_OUTLET, FORUM | "UAE is a model of Middle Eastern stability"; "Political Islam is inherently destabilizing"; "Human rights criticism is politically motivated" |
| 10 | Pakistani Kashmir Liberation Narrative | Pakistan | PAK | MEDIUM | IND, GBR, USA | STATE_MEDIA, SOCIAL_MEDIA, MESSAGING_APP | "Kashmir is an occupied territory"; "India commits genocide in Kashmir"; "UN resolutions demand plebiscite" |
| 11 | Belarusian Western Aggression Narrative | Belarus | BLR | MEDIUM | POL, LTU, LVA, DEU | STATE_MEDIA, NEWS_OUTLET | "Western neighbors are plotting regime change"; "NATO expansion threatens Belarusian sovereignty"; "Opposition is foreign-funded" |
| 12 | Chinese South China Sea Sovereignty | China | CHN | HIGH | PHL, VNM, MYS, USA, JPN | STATE_MEDIA, SOCIAL_MEDIA, NEWS_OUTLET, FORUM | "Nine-dash line is historical Chinese territory"; "Freedom of navigation patrols are provocations"; "ASEAN claimants lack legal standing" |
| 13 | Russian Africa Anti-Colonial Narrative | Russia | RUS | HIGH | MLI, BFA, NER, CAF, LBY | SOCIAL_MEDIA, STATE_MEDIA, MESSAGING_APP | "France is a neo-colonial oppressor"; "Wagner/Africa Corps provides real security"; "Western democracy is cultural imperialism" |
| 14 | Iranian Nuclear Program Justification | Iran | IRN | HIGH | USA, ISR, GBR, FRA, DEU | STATE_MEDIA, NEWS_OUTLET, SOCIAL_MEDIA | "Iran's nuclear program is peaceful"; "IAEA is a tool of Western imperialism"; "Nuclear technology is Iran's sovereign right" |
| 15 | Chinese Belt & Road Debt Diplomacy Counter-Narrative | China | CHN | MEDIUM | LKA, KEN, PAK, ETH, MYS | STATE_MEDIA, NEWS_OUTLET, SOCIAL_MEDIA | "Debt trap is a Western fabrication"; "BRI projects are mutually beneficial"; "Western infrastructure aid is conditional and exploitative" |

#### New Influence Campaigns

| # | Name | Actor | Sponsor | Confidence | Targets | Budget USD | Objectives |
|---|------|-------|---------|------------|---------|-----------|------------|
| 3 | Endless Mayfly | IRGC-linked entities | IRN | HIGH | USA, ISR, SAU, GBR | 8,000,000 | Discredit Saudi-Israeli normalization; Undermine US Middle East credibility; Amplify anti-Zionist sentiment |
| 4 | Ghostwriter | GRU Unit 26165 (Fancy Bear) | RUS | HIGH | POL, LTU, LVA, DEU | 12,000,000 | Undermine NATO Eastern Flank solidarity; Discredit Baltic governments; Fabricate internal NATO dissent |
| 5 | Spamouflage Dragon | PLA Strategic Support Force | CHN | MEDIUM | USA, TWN, AUS, CAN | 35,000,000 | Promote CCP narratives on YouTube/Facebook/X; Attack Chinese dissidents abroad; Discredit Uyghur genocide reporting |
| 6 | DPRK Crypto-Propaganda Hybrid | Lazarus Group / RGB | PRK | MEDIUM | KOR, JPN, USA | 5,000,000 | Fund regime through crypto theft; Spread pro-regime content on Korean-language social media; Discredit defector testimonies |
| 7 | Operation Doppelganger | GRU / Structura | RUS | HIGH | DEU, FRA, USA, UKR, ISR | 20,000,000 | Clone Western news sites with fabricated content; Undermine Western support for Ukraine; Amplify war fatigue narratives |
| 8 | Indian Chronicles | Srivastava Group (linked to Indian intelligence) | IND | MEDIUM | EU, UN, PAK, CHN | 3,000,000 | Influence EU parliament members on Kashmir; Create fake NGOs at UN Human Rights Council; Discredit Pakistan internationally |
| 9 | Turkish Troll Armies | AKP Social Media Operations | TUR | MEDIUM | GRC, FRA, DEU, NLD | 7,000,000 | Suppress Kurdish media narratives; Amplify Erdogan's image globally; Attack diaspora critics |
| 10 | Saudi Electronic Flies | Saudi Center for International Communications | SAU | MEDIUM | USA, GBR, TUR, QAT | 10,000,000 | Rehabilitate MBS image post-Khashoggi; Counter Qatar/Turkey media; Suppress human rights criticism |

#### New Disinformation Indicators

| # | Type | Title | Platform | Confidence | Linked Campaign | Verified |
|---|------|-------|----------|-----------|-----------------|---------|
| 4 | ASTROTURFING | Fabricated grassroots anti-NATO petition sites in Poland | SOCIAL_MEDIA | 0.850 | Ghostwriter | Yes |
| 5 | BOT_NETWORK | Spamouflage network of 10,000+ coordinated YouTube/X accounts | VIDEO_PLATFORM | 0.910 | Spamouflage Dragon | Yes |
| 6 | FABRICATED_DOCUMENT | Forged Saudi diplomatic cables leaked to anti-normalization outlets | NEWS_OUTLET | 0.780 | Endless Mayfly | Yes |
| 7 | STATE_MEDIA_AMPLIFICATION | RT Arabic / Sputnik synchronized amplification of Africa Corps narratives | STATE_MEDIA | 0.940 | Secondary Infektion | Yes |
| 8 | DEEPFAKE_CONTENT | AI-generated audio of Polish general discussing NATO withdrawal | MESSAGING_APP | 0.820 | Ghostwriter | No |
| 9 | CRYPTO_FRAUD | Lazarus Group phishing campaign disguised as Korean reunification charity | SOCIAL_MEDIA | 0.880 | DPRK Crypto-Propaganda | Yes |
| 10 | CLONE_WEBSITE | 37 cloned European news domains serving fabricated Ukraine war articles | NEWS_OUTLET | 0.960 | Operation Doppelganger | Yes |
| 11 | COORDINATED_INAUTHENTIC_BEHAVIOR | 2,400 fake Twitter accounts posing as Kashmiri civil society | SOCIAL_MEDIA | 0.810 | Indian Chronicles | Yes |
| 12 | BOT_NETWORK | AKP-linked bot network mass-reporting Kurdish journalists | SOCIAL_MEDIA | 0.870 | Turkish Troll Armies | No |
| 13 | ASTROTURFING | Saudi-funded think tank producing favorable MBS op-eds in Western media | NEWS_OUTLET | 0.750 | Saudi Electronic Flies | No |
| 14 | AI_GENERATED_CONTENT | GPT-generated "analyst commentary" on Chinese state media English portals | STATE_MEDIA | 0.830 | Spamouflage Dragon | Yes |
| 15 | HACK_AND_LEAK | Leaked (fabricated) emails attributed to Taiwanese defense officials | FORUM | 0.790 | Sharp Power Coalition | No |

#### New Attribution Assessments

| # | Subject | Attributed To | Confidence | Evidence Summary |
|---|---------|--------------|------------|-----------------|
| 1 | Energy FUD hashtag bot network (4,200 accounts) | GRU Unit 54777 (72nd Special Service Center) | HIGH | IP analysis traces to St. Petersburg troll farm infrastructure; posting patterns match known IRA/GRU TTPs; language analysis shows native Russian machine-translated content |
| 2 | Cloned European news domains (Doppelganger) | Structura National Technology (GRU contractor) | HIGH | Domain registration traces to Russian hosting providers; content mirrors known Structura operations; EU DisinfoLab investigation corroborates attribution |
| 3 | Spamouflage YouTube/X network | PLA Strategic Support Force, Unit 61398 | MEDIUM | Account creation patterns consistent with Chinese working hours; content aligns with CCP talking points; Mandiant and Meta investigations provide supporting evidence |
| 4 | Endless Mayfly fabricated documents | IRGC Quds Force — cyber division | HIGH | Domain infrastructure overlaps with known APT35/Charming Kitten; Citizen Lab investigation provides technical attribution; content targets align with IRGC strategic priorities |
| 5 | Indian Chronicles fake NGOs | Srivastava Group (New Delhi) | MEDIUM | EU DisinfoLab investigation identified 750+ fake media outlets; traced to single Indian entity; Indian government denied involvement |

### Data Sources for InfoOps Module

| Source | URL | Use |
|--------|-----|-----|
| CFR Cyber Operations Tracker | https://www.cfr.org/cyber-operations/ | State-sponsored cyber + influence ops database |
| MIT Cyber Operations Tracker | https://cyberir.mit.edu/site/cyber-operations-tracker/ | Academic attribution database |
| EU DisinfoLab | https://www.disinfo.eu/ | European disinformation investigations |
| Stanford Internet Observatory | https://cyber.fsi.stanford.edu/ | Academic research on information operations |
| Graphika Reports | https://graphika.com/reports | Network analysis of influence operations |
| Meta Adversarial Threat Reports | https://transparency.meta.com/en-gb/metasecurity/threat-reporting/ | Platform takedown reports with attribution |
| Wikipedia: Disinformation by Country | https://en.wikipedia.org/wiki/List_of_disinformation_attacks_by_country | Comprehensive reference list |
| NATO StratCom COE | https://stratcomcoe.org/ | NATO counter-disinformation research |
| CISA Nation-State Threats | https://www.cisa.gov/topics/cyber-threats-and-advisories/nation-state-cyber-actors | US government threat advisories |

---

## 3. Equipment Catalog Seed Data

### Current State

- `equipment_catalog` table exists in schema (`buildsheet.md` §5.1) but has no seed data in any migration file
- `equipment` table links unit inventories to catalog entries via `type_code`
- `specs` column is JSONB — fully flexible for per-category attributes

### Target: 270–450 Equipment Entries Across 7 Categories

### Category: Main Battle Tanks (ARMOR)

| Type Code | Name | Origin | Crew | Weight (t) | Speed (kph) | Range (km) | Main Gun (mm) | Armor Type | APS | Threat Score |
|-----------|------|--------|------|-----------|------------|-----------|---------------|------------|-----|-------------|
| MBT-M1A2SEP | M1A2 SEPv3 Abrams | USA | 4 | 73.6 | 67 | 426 | 120 L/44 | Chobham/DU composite | Trophy | 0.92 |
| MBT-LEO2A7 | Leopard 2A7+ | DEU | 4 | 67.0 | 68 | 450 | 120 L/55 | Composite + AMAP | Trophy | 0.90 |
| MBT-CHALL3 | Challenger 3 | GBR | 4 | 66.0 | 60 | 450 | 120 L/55 | Chobham/Dorchester | Trophy | 0.88 |
| MBT-LECLERC | Leclerc S2 | FRA | 3 | 57.0 | 71 | 550 | 120 L/52 | Composite modular | — | 0.85 |
| MBT-MERKAVA4 | Merkava Mk 4M Windbreaker | ISR | 4 | 65.0 | 64 | 500 | 120 L/44 | Composite modular | Trophy | 0.91 |
| MBT-K2 | K2 Black Panther | KOR | 3 | 55.0 | 70 | 450 | 120 L/55 | Composite + ERA | KAPS | 0.87 |
| MBT-TYPE10 | Type 10 Hitomaru | JPN | 3 | 44.0 | 70 | 440 | 120 L/44 | Composite modular | — | 0.84 |
| MBT-T90M | T-90M Proryv | RUS | 3 | 48.0 | 60 | 550 | 125 2A46M-5 | Relikt ERA + composite | Shtora-1 | 0.82 |
| MBT-T80BVM | T-80BVM | RUS | 3 | 46.0 | 70 | 440 | 125 2A46M-4 | Relikt ERA | — | 0.75 |
| MBT-T72B3 | T-72B3M | RUS | 3 | 46.5 | 60 | 500 | 125 2A46M-5 | Kontakt-5 ERA | — | 0.70 |
| MBT-T14 | T-14 Armata | RUS | 3 | 55.0 | 80 | 500 | 125 2A82-1M | Malachit ERA + composite | Afghanit | 0.85 |
| MBT-TYPE99A | Type 99A | CHN | 3 | 58.0 | 80 | 600 | 125 ZPT-98 | Composite + ERA | GL-5 | 0.80 |
| MBT-TYPE15 | Type 15 (ZTQ-15) | CHN | 3 | 36.0 | 70 | 450 | 105 rifled | Composite modular | — | 0.65 |
| MBT-ARJUN2 | Arjun Mk 2 | IND | 4 | 68.0 | 58 | 500 | 120 rifled | Kanchan composite | — | 0.72 |
| MBT-ALTAY | Altay | TUR | 4 | 65.0 | 65 | 450 | 120 L/55 | Composite modular | PULAT | 0.78 |
| MBT-OPLOT | T-84 Oplot-M | UKR | 3 | 51.0 | 65 | 540 | 125 KBA-3 | Nozh ERA + composite | Varta | 0.76 |
| MBT-PT91 | PT-91 Twardy | POL | 3 | 45.9 | 60 | 400 | 125 2A46 | ERAWA ERA | — | 0.68 |
| MBT-ALKHALD | Al-Khalid I | PAK | 3 | 48.0 | 65 | 400 | 125 smoothbore | Composite + ERA | — | 0.70 |

### Category: Infantry Fighting Vehicles / APCs (IFV)

| Type Code | Name | Origin | Crew+Dismounts | Weight (t) | Speed (kph) | Armament | Amphibious | Threat Score |
|-----------|------|--------|---------------|-----------|------------|----------|-----------|-------------|
| IFV-M2A3 | M2A3 Bradley | USA | 3+6 | 33.6 | 61 | 25mm M242 + TOW-2B | No | 0.85 |
| IFV-PUMA | Puma | DEU | 3+6 | 43.0 | 70 | 30mm MK 30-2 + Spike LR | No | 0.88 |
| IFV-WARRIOR | Warrior CSP | GBR | 3+7 | 28.0 | 75 | 40mm CTAS | No | 0.80 |
| IFV-VBCI | VBCI 2 | FRA | 3+9 | 29.0 | 100 | 25mm M811 | No | 0.78 |
| IFV-CV90 | CV90 Mk IV | SWE | 3+8 | 37.0 | 70 | 35mm Bushmaster III | No | 0.86 |
| IFV-BMP3 | BMP-3 | RUS | 3+7 | 18.7 | 70 | 100mm 2A70 + 30mm 2A72 | Yes | 0.75 |
| IFV-BMP2M | BMP-2M Berezhok | RUS | 3+7 | 14.3 | 65 | 30mm 2A42 + Kornet | Yes | 0.72 |
| IFV-ZBD04A | ZBD-04A | CHN | 3+7 | 24.5 | 65 | 100mm rifled + 30mm auto | Yes | 0.73 |
| IFV-NAMER | Namer | ISR | 3+9 | 60.0 | 60 | 30mm Mk 44 + Trophy | No | 0.90 |
| IFV-K21 | K21 | KOR | 3+9 | 25.6 | 70 | 40mm L/70 | Yes | 0.80 |
| IFV-LYNX | KF41 Lynx | DEU | 3+8 | 44.0 | 65 | 35mm Wotan + Spike LR | No | 0.87 |
| APC-STRYKER | Stryker M1126 | USA | 2+9 | 18.6 | 97 | 12.7mm M2 or 30mm MCT-30 | No | 0.70 |
| APC-BOXER | Boxer CRV | DEU/NLD | 2+8 | 38.0 | 103 | 30mm Mk 44 (CRV variant) | No | 0.82 |
| APC-PATRIA | Patria AMV XP | FIN | 2+10 | 30.0 | 100 | Configurable turret | Yes | 0.75 |
| APC-BTR82A | BTR-82A | RUS | 3+7 | 15.4 | 80 | 30mm 2A72 | Yes | 0.60 |

### Category: Fighter / Attack Aircraft (AIRCRAFT)

| Type Code | Name | Origin | Crew | Max Speed (kph) | Combat Radius (km) | Ceiling (m) | Payload (kg) | Stealth | Gen | Threat Score |
|-----------|------|--------|------|----------------|-------------------|------------|-------------|---------|-----|-------------|
| FTR-F35A | F-35A Lightning II | USA | 1 | 1,960 | 1,093 | 15,240 | 8,160 | Yes | 5th | 0.95 |
| FTR-F35B | F-35B Lightning II | USA | 1 | 1,960 | 935 | 15,240 | 6,800 | Yes | 5th | 0.93 |
| FTR-F22 | F-22A Raptor | USA | 1 | 2,410 | 759 | 19,812 | 10,000 | Yes | 5th | 0.97 |
| FTR-F15EX | F-15EX Eagle II | USA | 1–2 | 2,665 | 1,270 | 19,812 | 11,113 | No | 4.5th | 0.88 |
| FTR-F16V | F-16V Viper | USA | 1 | 2,120 | 546 | 15,240 | 7,700 | No | 4th | 0.78 |
| FTR-FA18EF | F/A-18E/F Super Hornet | USA | 1–2 | 1,915 | 722 | 15,240 | 8,050 | No | 4.5th | 0.82 |
| FTR-TYPHOON | Eurofighter Typhoon Tranche 4 | EUR | 1–2 | 2,495 | 1,389 | 16,764 | 9,000 | No | 4.5th | 0.86 |
| FTR-RAFALE | Dassault Rafale F4 | FRA | 1–2 | 1,912 | 1,093 | 15,235 | 9,500 | No | 4.5th | 0.87 |
| FTR-GRIPEN | JAS 39E Gripen | SWE | 1 | 2,204 | 800 | 15,240 | 5,300 | No | 4.5th | 0.80 |
| FTR-SU57 | Su-57 Felon | RUS | 1 | 2,600 | 1,500 | 20,000 | 10,000 | Yes | 5th | 0.85 |
| FTR-SU35S | Su-35S Flanker-E | RUS | 1 | 2,500 | 1,580 | 18,000 | 8,000 | No | 4++ | 0.83 |
| FTR-SU34 | Su-34 Fullback | RUS | 2 | 1,900 | 1,100 | 15,000 | 12,000 | No | 4+ | 0.78 |
| FTR-MIG35 | MiG-35 Fulcrum-F | RUS | 1–2 | 2,400 | 1,000 | 17,500 | 7,000 | No | 4++ | 0.75 |
| FTR-J20 | J-20 Mighty Dragon | CHN | 1 | 2,100 | 1,100 | 20,000 | 8,000 | Yes | 5th | 0.84 |
| FTR-J16 | J-16 | CHN | 2 | 2,400 | 1,500 | 17,000 | 12,000 | No | 4.5th | 0.79 |
| FTR-J10C | J-10C Vigorous Dragon | CHN | 1 | 2,200 | 550 | 18,000 | 6,000 | No | 4th | 0.73 |
| FTR-KF21 | KF-21 Boramae | KOR | 1–2 | 1,960 | 800 | 16,800 | 7,700 | Reduced | 4.5th | 0.80 |
| FTR-TEJAS2 | HAL Tejas Mk 2 | IND | 1 | 1,850 | 500 | 15,250 | 5,500 | No | 4th | 0.68 |
| ATK-A10C | A-10C Thunderbolt II | USA | 1 | 706 | 460 | 13,636 | 7,260 | No | — | 0.75 |
| ATK-SU25SM3 | Su-25SM3 Frogfoot | RUS | 1 | 975 | 375 | 10,000 | 4,400 | No | — | 0.65 |

### Category: Attack / Utility Helicopters (HELICOPTER)

| Type Code | Name | Origin | Crew | Max Speed (kph) | Combat Radius (km) | Armament | Threat Score |
|-----------|------|--------|------|----------------|-------------------|----------|-------------|
| HEL-AH64E | AH-64E Apache Guardian | USA | 2 | 293 | 480 | 30mm M230 + Hellfire + Hydra 70 | 0.92 |
| HEL-AH1Z | AH-1Z Viper | USA | 2 | 337 | 231 | 20mm M197 + Hellfire + AIM-9 | 0.85 |
| HEL-TIGER | Tiger HAD | FRA/DEU | 2 | 290 | 400 | 30mm GIAT + Hellfire/HOT/Trigat | 0.82 |
| HEL-KA52 | Ka-52 Alligator | RUS | 2 | 310 | 460 | 30mm 2A42 + Vikhr + Ataka | 0.83 |
| HEL-MI28NM | Mi-28NM Night Hunter | RUS | 2 | 300 | 450 | 30mm 2A42 + Ataka + Khrizantema | 0.80 |
| HEL-Z10 | Z-10 | CHN | 2 | 270 | 400 | 23mm cannon + HJ-10 | 0.72 |
| HEL-T129 | T129 ATAK | TUR | 2 | 278 | 561 | 20mm M197 + UMTAS/Cirit | 0.75 |
| HEL-UH60M | UH-60M Black Hawk | USA | 4 | 294 | 590 | Door guns + pylons | 0.70 |
| HEL-MI8AMT | Mi-8AMTSh Terminator | RUS | 3 | 250 | 580 | B-8V20A rockets + Ataka | 0.68 |
| HEL-AW149 | AW149 | ITA/GBR | 2 | 290 | 700 | Configurable | 0.72 |

### Category: Naval Combatants (NAVAL)

| Type Code | Name | Origin | Crew | Displacement (t) | Speed (kts) | Range (nm) | VLS Cells | Radar | Threat Score |
|-----------|------|--------|------|-----------------|------------|-----------|-----------|-------|-------------|
| DDG-ARLEIGH3 | Arleigh Burke Flight III | USA | 329 | 9,700 | 30 | 4,400 | 96 | SPY-6(V)1 AMDR | 0.92 |
| DDG-TYPE45 | Type 45 Daring | GBR | 191 | 8,500 | 29 | 7,000 | 48 (Sylver) | SAMPSON AESA | 0.85 |
| DDG-FREMM | FREMM Aquitaine | FRA/ITA | 108 | 6,000 | 27 | 6,000 | 16 (Sylver A50) + 16 (Aster) | Herakles | 0.83 |
| DDG-TYPE055 | Type 055 Renhai | CHN | 280 | 13,000 | 30 | 5,000 | 112 | Type 346B AESA | 0.88 |
| DDG-TYPE052D | Type 052D Luyang III | CHN | 280 | 7,500 | 30 | 4,500 | 64 | Type 346A AESA | 0.82 |
| DDG-GORSHKOV | Admiral Gorshkov (Pr. 22350) | RUS | 210 | 5,400 | 29 | 4,500 | 32 (3S14 UKSK) | Poliment-Redut | 0.80 |
| FFG-CONSTELLATION | Constellation-class | USA | 200 | 7,300 | 26 | 6,000 | 32 (Mk 41) | SPY-6(V)3 | 0.84 |
| FFG-TYPE26 | Type 26 City | GBR | 157 | 6,900 | 26 | 7,000 | 24 (Mk 41) + 48 (Sea Ceptor) | Artisan 3D + S2150 | 0.86 |
| FFG-F126 | F126 Baden-Württemberg | DEU | 114 | 9,000 | 26 | 4,000 | 8 (Mk 41) | TRS-4D AESA | 0.78 |
| SSN-VIRGINIA | Virginia Block V | USA | 135 | 10,200 | 25+ | Unlimited (nuclear) | 40 VPM | BYG-1 | 0.95 |
| SSN-ASTUTE | Astute-class | GBR | 98 | 7,800 | 29+ | Unlimited (nuclear) | — (38 weapons) | Sonar 2076 | 0.90 |
| SSN-SUFFREN | Suffren (Barracuda) | FRA | 65 | 5,300 | 25+ | Unlimited (nuclear) | — (F21 + MdCN) | — | 0.87 |
| SSN-YASEN | Yasen-M (Pr. 885M) | RUS | 64 | 13,800 | 31+ | Unlimited (nuclear) | 32 (3M55/3M22) | Irtysh-Amfora | 0.88 |
| SSBN-COLUMBIA | Columbia-class | USA | 155 | 20,800 | 20+ | Unlimited (nuclear) | 16 Trident II D5LE | — | 0.98 |
| CVN-FORD | Gerald R. Ford (CVN-78) | USA | 4,660 | 100,000 | 30+ | Unlimited (nuclear) | ESSM + RIM-116 | DBR (SPY-3 + SPY-4) | 0.99 |
| CV-LIAONING | Liaoning (Type 001) | CHN | 2,000 | 67,500 | 32 | 3,850 | HHQ-10 | Type 346 | 0.72 |
| CV-FUJIAN | Fujian (Type 003) | CHN | ~2,500 | 80,000 | 30+ | — | — | Type 346B | 0.82 |

### Category: Air Defense / Missile Systems (MISSILE)

| Type Code | Name | Origin | Range (km) | Ceiling (m) | Missiles/Battery | Target Types | Threat Score |
|-----------|------|--------|-----------|------------|-----------------|-------------|-------------|
| SAM-PATRIOT | MIM-104 Patriot PAC-3 MSE | USA | 150 | 24,000 | 16 per launcher | Aircraft, TBM, cruise missile | 0.90 |
| SAM-THAAD | THAAD | USA | 200 | 150,000 | 48 per battery | TBM, IRBM exo-atmospheric | 0.92 |
| SAM-NASAMS | NASAMS 3 | NOR/USA | 40 | 16,000 | 6 per launcher | Aircraft, cruise missile, UAV | 0.75 |
| SAM-IHDP | Iron Dome + David's Sling | ISR | 70 (DS) / 10 (ID) | 15,000 | Variable | Rockets, artillery, cruise missiles, TBM | 0.88 |
| SAM-ASTER30 | SAMP/T Aster 30 | FRA/ITA | 120 | 20,000 | 48 per battery | Aircraft, TBM, cruise missile | 0.85 |
| SAM-S400 | S-400 Triumf | RUS | 400 | 30,000 | 4 × 4 per battery | Aircraft, cruise missile, TBM | 0.88 |
| SAM-S300V4 | S-300V4 Antey-2500 | RUS | 400 | 37,000 | 4 per TEL | TBM, IRBM, aircraft | 0.84 |
| SAM-S350 | S-350 Vityaz | RUS | 120 | 30,000 | 12 per launcher | Aircraft, cruise missile | 0.78 |
| SAM-BUK3M | Buk-M3 Viking | RUS | 70 | 25,000 | 6 per TELAR | Aircraft, cruise missile, TBM | 0.80 |
| SAM-PANTSIR | Pantsir-S1M | RUS | 20 (missile) / 4 (gun) | 15,000 | 12 + 2×30mm | Aircraft, cruise missile, UAV, PGM | 0.72 |
| SAM-HQ9B | HQ-9B | CHN | 300 | 27,000 | 4 per TEL | Aircraft, cruise missile, TBM | 0.82 |
| SAM-HQ22 | HQ-22 | CHN | 170 | 27,000 | 4 per TEL | Aircraft, cruise missile | 0.76 |
| SAM-CHEOLMAE | Cheolmae-II (M-SAM) | KOR | 40 | 15,000 | 6 per launcher | Aircraft, cruise missile | 0.74 |
| BM-MINUTEMAN | LGM-30G Minuteman III | USA | 13,000 | — | 1 per silo | Strategic ICBM (W87 warhead) | 0.95 |
| BM-TRIDENT | UGM-133A Trident II D5LE | USA | 12,000 | — | 4–5 per SSBN tube | Strategic SLBM (W76-1/W88) | 0.98 |
| BM-DF41 | DF-41 (CSS-20) | CHN | 15,000 | — | MIRV 10 | Strategic ICBM, TEL road-mobile | 0.92 |
| BM-DF21D | DF-21D (CSS-5 Mod 4) | CHN | 1,500 | — | 1 per TEL | ASBM (carrier killer) | 0.80 |
| BM-TOPOL | RS-24 Yars (Topol-M) | RUS | 12,000 | — | MIRV 4 | Strategic ICBM, TEL road-mobile | 0.90 |
| BM-SARMAT | RS-28 Sarmat (Satan II) | RUS | 18,000 | — | MIRV 10–15 | Strategic ICBM, silo-based | 0.93 |
| BM-HWASONG18 | Hwasong-18 | PRK | 15,000 | — | 1 per TEL | Strategic ICBM, solid-fuel | 0.65 |
| CM-TOMAHAWK | BGM-109 Tomahawk Block V | USA | 1,600 | — | Per VLS cell | Land attack cruise missile | 0.88 |
| CM-SCALP | SCALP-EG / Storm Shadow | FRA/GBR | 560 | — | Per aircraft pylon | Land attack cruise missile, stealth | 0.82 |
| CM-KALIBR | 3M-14 Kalibr | RUS | 1,500–2,500 | — | Per VLS cell | Land attack cruise missile | 0.80 |
| HGV-DF17 | DF-ZF (DF-17 glide vehicle) | CHN | 2,500 | — | 1 per TEL | Hypersonic glide vehicle | 0.85 |
| HGV-AVANGARD | Avangard (Yu-74) | RUS | 6,000+ | — | 1 per ICBM booster | Hypersonic glide vehicle | 0.88 |
| CM-BRAHMOS2 | BrahMos-II | IND/RUS | 600 | — | Per launcher | Hypersonic cruise missile | 0.78 |

### Category: Artillery / Rocket Systems (ARTILLERY)

| Type Code | Name | Origin | Caliber (mm) | Range (km) | Rate (rds/min) | Crew | Mobility | Threat Score |
|-----------|------|--------|-------------|-----------|---------------|------|---------|-------------|
| SPH-M109A7 | M109A7 Paladin | USA | 155 | 30 (base) / 40 (RAP) | 4 | 4 | Tracked SP | 0.78 |
| SPH-PZH2000 | PzH 2000 | DEU | 155 | 40 (base) / 56 (Vulcano) | 9 | 5 | Tracked SP | 0.88 |
| SPH-CAESAR2 | CAESAR Mk 2 | FRA | 155 | 42 (base) / 50+ (ERFB) | 6 | 4 | Wheeled (8×8) SP | 0.82 |
| SPH-K9A2 | K9A2 Thunder | KOR | 155 | 40 (base) / 54 (K315 ERM) | 6 | 3 | Tracked SP | 0.85 |
| SPH-ARCHER | Archer FH77BW L52 | SWE | 155 | 40 (base) / 60 (Excalibur) | 9 (burst) | 2–4 | Wheeled (6×6) SP | 0.84 |
| SPH-2S19M2 | 2S19M2 Msta-S | RUS | 152 | 29 (base) / 36 (RAP) | 8 | 5 | Tracked SP | 0.72 |
| SPH-2S35 | 2S35 Koalitsiya-SV | RUS | 152 | 40 (base) / 70 (guided) | 12 | 2 | Tracked SP | 0.80 |
| SPH-PLZ05 | PLZ-05A | CHN | 155 | 39 (base) / 53 (ERFB-BB) | 8 | 4 | Tracked SP | 0.76 |
| MLRS-HIMARS | M142 HIMARS | USA | 227mm / ATACMS / PrSM | 300 (GMLRS) / 500 (PrSM) | 6 rkt pod | 3 | Wheeled (6×6) | 0.90 |
| MLRS-M270 | M270A2 MLRS | USA | 227mm / ATACMS | 300 (GMLRS) / 300 (ATACMS) | 12 rkt pod | 3 | Tracked | 0.88 |
| MLRS-BM30 | BM-30 Smerch (9A52-4) | RUS | 300mm | 90 (base) / 120 (9M542) | 12 tube | 4 | Wheeled (8×8) | 0.78 |
| MLRS-BM21 | BM-21 Grad | RUS | 122mm | 40 | 40 tube | 3 | Wheeled (6×6) | 0.55 |
| MLRS-PHL03 | PHL-03A | CHN | 300mm | 130 | 12 tube | 4 | Wheeled (8×8) | 0.76 |
| MRT-120 | M120 Mortar (Rifled 120mm) | USA | 120 | 7.2 | 4 | 4 | Towed | 0.45 |

### JSONB `specs` Field Templates by Category

```json
// ARMOR template
{
  "crew": 3,
  "weight_tons": 48.0,
  "speed_kph": 60,
  "range_km": 550,
  "main_gun_mm": 125,
  "main_gun_designation": "2A46M-5",
  "armor_type": "Relikt ERA + composite",
  "aps": "Shtora-1",
  "night_vision": true,
  "nbc_protection": true,
  "engine_hp": 1130,
  "generation": "3+"
}

// AIRCRAFT template
{
  "crew": 1,
  "max_speed_kph": 1960,
  "combat_radius_km": 1093,
  "ceiling_m": 15240,
  "weapons_payload_kg": 8160,
  "stealth": true,
  "generation": "5th",
  "radar": "AN/APG-81 AESA",
  "ew_suite": "AN/ASQ-239",
  "hardpoints": 10,
  "internal_weapons_bay": true
}

// NAVAL template
{
  "crew": 329,
  "displacement_tons": 9700,
  "speed_kts": 30,
  "range_nm": 4400,
  "vls_cells": 96,
  "radar": "SPY-6(V)1 AMDR",
  "sonar": "AN/SQQ-89A(V)15",
  "helicopter": 2,
  "propulsion": "gas_turbine",
  "ciws": "Phalanx + SeaRAM"
}

// MISSILE template
{
  "range_km": 400,
  "ceiling_m": 30000,
  "missiles_per_battery": 4,
  "radar_detection_km": 600,
  "target_types": ["aircraft", "cruise_missile", "ballistic_missile"],
  "guidance": "semi-active + active",
  "mobility": "TEL road-mobile",
  "reload_time_min": 15
}

// ARTILLERY template
{
  "caliber_mm": 155,
  "range_km_base": 40,
  "range_km_extended": 56,
  "rate_of_fire_rpm": 9,
  "crew": 5,
  "mobility_type": "tracked_sp",
  "ammunition_types": ["HE", "smoke", "illumination", "DPICM", "guided"],
  "autoloader": true,
  "engine_hp": 1000
}
```

### Data Sources for Equipment Catalog

| Source | URL | Access | Best For |
|--------|-----|--------|----------|
| Acuity Lab Military API | https://www.acuitylab.net/military | REST API (free) | Structured JSON specs — direct ingest |
| ODIN (TRADOC) Worldwide Equipment Guide | https://odin.tradoc.army.mil/WEG | Web (request API) | Most authoritative threat equipment data |
| GlobalMilitary.net | https://www.globalmilitary.net/ | Web | Country-level inventories, 450+ aircraft |
| Military Periscope | https://www.militaryperiscope.com/ | Web (registration) | Comprehensive weapon system database |
| SIPRI Arms Transfers DB | https://www.sipri.org/databases/armstransfers | CSV export | Who sold what to whom |
| AFV Database | https://afvdatabase.com/ | Web | US armored vehicle detailed specs |
| IISS Military Balance | https://www.iiss.org/publications/the-military-balance/ | Licensed (annual) | Gold standard OOB + equipment counts |
| Jane's Defence | https://www.janes.com/ | Licensed | Platform specs, country-level inventories |
| OpenAircraftType (GitHub) | https://github.com/atoff/OpenAircraftType | Open source | Aircraft type classification database |
| DoD Public Data Listing | https://data.defense.gov/Public-Data-Listing/ | Public (JSON) | Official US defense datasets |

---

## Implementation Plan

### Migration Files to Create

| File | Content | Estimated Rows |
|------|---------|---------------|
| `017_econ_seed_expansion.sql` | 15–20 new sanction targets, 15 new trade routes, 25 new economic indicators | ~60 INSERTs |
| `018_infoops_seed_expansion.sql` | 12 new narratives, 8 new campaigns, 12 new indicators, 5 attribution assessments | ~37 INSERTs |
| `019_equipment_catalog_seed.sql` | Full equipment catalog across 7 categories | ~180–300 INSERTs |

### Implementation Order

1. **Equipment catalog** (019) — highest simulation value; feeds directly into `sim-engine` combat resolution
2. **Econ sanctions** (017) — broadest data expansion; mostly additive INSERTs
3. **InfoOps** (018) — enriches narrative analysis; requires careful attribution sourcing

### Validation Checklist

- [ ] All `country_code` values exist in `countries` table (or add missing countries to `002_seed_countries.sql`)
- [ ] All `ON CONFLICT DO NOTHING` to ensure idempotent re-runs
- [ ] All JSONB arrays properly escaped
- [ ] `scripts/db-migrate-smoke.sh` passes with new migrations
- [ ] Frontend filter/search UI handles increased data volume without performance regression
- [ ] Equipment `type_code` values are unique and follow `CATEGORY-DESIGNATION` pattern

---

*All data in this document is UNCLASSIFIED and derived from open sources.*
