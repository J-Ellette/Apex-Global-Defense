-- =============================================================================
-- 019_equipment_catalog_seed.sql
-- Equipment catalog seed expansion (ARMOR, IFV/APC, AIRCRAFT, HELICOPTER, NAVAL, MISSILE, ARTILLERY)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- ARMOR (Main Battle Tanks)
-- ---------------------------------------------------------------------------
INSERT INTO equipment_catalog (
    type_code, category, name, origin_country, specs, threat_score, in_service_year
) VALUES
    ('MBT-M1A2SEP','ARMOR','M1A2 SEPv3 Abrams','USA',jsonb_build_object('crew',4,'weight_tons',73.6,'speed_kph',67,'range_km',426,'main_gun','120 L/44','armor_type','Chobham/DU composite','aps','Trophy'),0.92,2017),
    ('MBT-LEO2A7','ARMOR','Leopard 2A7+','DEU',jsonb_build_object('crew',4,'weight_tons',67.0,'speed_kph',68,'range_km',450,'main_gun','120 L/55','armor_type','Composite + AMAP','aps','Trophy'),0.90,2014),
    ('MBT-CHALL3','ARMOR','Challenger 3','GBR',jsonb_build_object('crew',4,'weight_tons',66.0,'speed_kph',60,'range_km',450,'main_gun','120 L/55','armor_type','Chobham/Dorchester','aps','Trophy'),0.88,2025),
    ('MBT-LECLERC','ARMOR','Leclerc S2','FRA',jsonb_build_object('crew',3,'weight_tons',57.0,'speed_kph',71,'range_km',550,'main_gun','120 L/52','armor_type','Composite modular','aps',NULL),0.85,1998),
    ('MBT-MERKAVA4','ARMOR','Merkava Mk 4M Windbreaker','ISR',jsonb_build_object('crew',4,'weight_tons',65.0,'speed_kph',64,'range_km',500,'main_gun','120 L/44','armor_type','Composite modular','aps','Trophy'),0.91,2011),
    ('MBT-K2','ARMOR','K2 Black Panther','KOR',jsonb_build_object('crew',3,'weight_tons',55.0,'speed_kph',70,'range_km',450,'main_gun','120 L/55','armor_type','Composite + ERA','aps','KAPS'),0.87,2014),
    ('MBT-TYPE10','ARMOR','Type 10 Hitomaru','JPN',jsonb_build_object('crew',3,'weight_tons',44.0,'speed_kph',70,'range_km',440,'main_gun','120 L/44','armor_type','Composite modular','aps',NULL),0.84,2012),
    ('MBT-T90M','ARMOR','T-90M Proryv','RUS',jsonb_build_object('crew',3,'weight_tons',48.0,'speed_kph',60,'range_km',550,'main_gun','125 2A46M-5','armor_type','Relikt ERA + composite','aps','Shtora-1'),0.82,2020),
    ('MBT-T80BVM','ARMOR','T-80BVM','RUS',jsonb_build_object('crew',3,'weight_tons',46.0,'speed_kph',70,'range_km',440,'main_gun','125 2A46M-4','armor_type','Relikt ERA','aps',NULL),0.75,2018),
    ('MBT-T72B3','ARMOR','T-72B3M','RUS',jsonb_build_object('crew',3,'weight_tons',46.5,'speed_kph',60,'range_km',500,'main_gun','125 2A46M-5','armor_type','Kontakt-5 ERA','aps',NULL),0.70,2016),
    ('MBT-T14','ARMOR','T-14 Armata','RUS',jsonb_build_object('crew',3,'weight_tons',55.0,'speed_kph',80,'range_km',500,'main_gun','125 2A82-1M','armor_type','Malachit ERA + composite','aps','Afghanit'),0.85,2021),
    ('MBT-TYPE99A','ARMOR','Type 99A','CHN',jsonb_build_object('crew',3,'weight_tons',58.0,'speed_kph',80,'range_km',600,'main_gun','125 ZPT-98','armor_type','Composite + ERA','aps','GL-5'),0.80,2011),
    ('MBT-TYPE15','ARMOR','Type 15 (ZTQ-15)','CHN',jsonb_build_object('crew',3,'weight_tons',36.0,'speed_kph',70,'range_km',450,'main_gun','105 rifled','armor_type','Composite modular','aps',NULL),0.65,2019),
    ('MBT-ARJUN2','ARMOR','Arjun Mk 2','IND',jsonb_build_object('crew',4,'weight_tons',68.0,'speed_kph',58,'range_km',500,'main_gun','120 rifled','armor_type','Kanchan composite','aps',NULL),0.72,2021),
    ('MBT-ALTAY','ARMOR','Altay','TUR',jsonb_build_object('crew',4,'weight_tons',65.0,'speed_kph',65,'range_km',450,'main_gun','120 L/55','armor_type','Composite modular','aps','PULAT'),0.78,2025),
    ('MBT-OPLOT','ARMOR','T-84 Oplot-M','UKR',jsonb_build_object('crew',3,'weight_tons',51.0,'speed_kph',65,'range_km',540,'main_gun','125 KBA-3','armor_type','Nozh ERA + composite','aps','Varta'),0.76,2009),
    ('MBT-PT91','ARMOR','PT-91 Twardy','POL',jsonb_build_object('crew',3,'weight_tons',45.9,'speed_kph',60,'range_km',400,'main_gun','125 2A46','armor_type','ERAWA ERA','aps',NULL),0.68,1995),
    ('MBT-ALKHALD','ARMOR','Al-Khalid I','PAK',jsonb_build_object('crew',3,'weight_tons',48.0,'speed_kph',65,'range_km',400,'main_gun','125 smoothbore','armor_type','Composite + ERA','aps',NULL),0.70,2020)
ON CONFLICT (type_code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- HELICOPTER (Attack / Utility)
-- ---------------------------------------------------------------------------
INSERT INTO equipment_catalog (
    type_code, category, name, origin_country, specs, threat_score, in_service_year
) VALUES
    ('HEL-AH64E','HELICOPTER','AH-64E Apache Guardian','USA',jsonb_build_object('crew',2,'max_speed_kph',293,'combat_radius_km',480,'armament','30mm M230 + Hellfire + Hydra 70'),0.92,2012),
    ('HEL-AH1Z','HELICOPTER','AH-1Z Viper','USA',jsonb_build_object('crew',2,'max_speed_kph',337,'combat_radius_km',231,'armament','20mm M197 + Hellfire + AIM-9'),0.85,2010),
    ('HEL-TIGER','HELICOPTER','Tiger HAD','FRA',jsonb_build_object('crew',2,'max_speed_kph',290,'combat_radius_km',400,'armament','30mm GIAT + Hellfire/HOT/Trigat'),0.82,2013),
    ('HEL-KA52','HELICOPTER','Ka-52 Alligator','RUS',jsonb_build_object('crew',2,'max_speed_kph',310,'combat_radius_km',460,'armament','30mm 2A42 + Vikhr + Ataka'),0.83,2011),
    ('HEL-MI28NM','HELICOPTER','Mi-28NM Night Hunter','RUS',jsonb_build_object('crew',2,'max_speed_kph',300,'combat_radius_km',450,'armament','30mm 2A42 + Ataka + Khrizantema'),0.80,2019),
    ('HEL-Z10','HELICOPTER','Z-10','CHN',jsonb_build_object('crew',2,'max_speed_kph',270,'combat_radius_km',400,'armament','23mm cannon + HJ-10'),0.72,2012),
    ('HEL-T129','HELICOPTER','T129 ATAK','TUR',jsonb_build_object('crew',2,'max_speed_kph',278,'combat_radius_km',561,'armament','20mm M197 + UMTAS/Cirit'),0.75,2014),
    ('HEL-UH60M','HELICOPTER','UH-60M Black Hawk','USA',jsonb_build_object('crew',4,'max_speed_kph',294,'combat_radius_km',590,'armament','Door guns + pylons'),0.70,2006),
    ('HEL-MI8AMT','HELICOPTER','Mi-8AMTSh Terminator','RUS',jsonb_build_object('crew',3,'max_speed_kph',250,'combat_radius_km',580,'armament','B-8V20A rockets + Ataka'),0.68,2010),
    ('HEL-AW149','HELICOPTER','AW149','ITA',jsonb_build_object('crew',2,'max_speed_kph',290,'combat_radius_km',700,'armament','Configurable'),0.72,2017)
ON CONFLICT (type_code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- NAVAL (Surface combatants, submarines, carriers)
-- ---------------------------------------------------------------------------
INSERT INTO equipment_catalog (
    type_code, category, name, origin_country, specs, threat_score, in_service_year
) VALUES
    ('DDG-ARLEIGH3','NAVAL','Arleigh Burke Flight III','USA',jsonb_build_object('crew',329,'displacement_tons',9700,'speed_kts','30','range_nm','4400','vls_cells','96','radar','SPY-6(V)1 AMDR'),0.92,2023),
    ('DDG-TYPE45','NAVAL','Type 45 Daring','GBR',jsonb_build_object('crew',191,'displacement_tons',8500,'speed_kts','29','range_nm','7000','vls_cells','48 (Sylver)','radar','SAMPSON AESA'),0.85,2009),
    ('DDG-FREMM','NAVAL','FREMM Aquitaine','FRA',jsonb_build_object('crew',108,'displacement_tons',6000,'speed_kts','27','range_nm','6000','vls_cells','16 (Sylver A50) + 16 (Aster)','radar','Herakles'),0.83,2012),
    ('DDG-TYPE055','NAVAL','Type 055 Renhai','CHN',jsonb_build_object('crew',280,'displacement_tons',13000,'speed_kts','30','range_nm','5000','vls_cells','112','radar','Type 346B AESA'),0.88,2020),
    ('DDG-TYPE052D','NAVAL','Type 052D Luyang III','CHN',jsonb_build_object('crew',280,'displacement_tons',7500,'speed_kts','30','range_nm','4500','vls_cells','64','radar','Type 346A AESA'),0.82,2014),
    ('DDG-GORSHKOV','NAVAL','Admiral Gorshkov (Pr. 22350)','RUS',jsonb_build_object('crew',210,'displacement_tons',5400,'speed_kts','29','range_nm','4500','vls_cells','32 (3S14 UKSK)','radar','Poliment-Redut'),0.80,2018),
    ('FFG-CONSTELLATION','NAVAL','Constellation-class','USA',jsonb_build_object('crew',200,'displacement_tons',7300,'speed_kts','26','range_nm','6000','vls_cells','32 (Mk 41)','radar','SPY-6(V)3'),0.84,2028),
    ('FFG-TYPE26','NAVAL','Type 26 City','GBR',jsonb_build_object('crew',157,'displacement_tons',6900,'speed_kts','26','range_nm','7000','vls_cells','24 (Mk 41) + 48 (Sea Ceptor)','radar','Artisan 3D + S2150'),0.86,2028),
    ('FFG-F126','NAVAL','F126 Baden-Württemberg','DEU',jsonb_build_object('crew',114,'displacement_tons',9000,'speed_kts','26','range_nm','4000','vls_cells','8 (Mk 41)','radar','TRS-4D AESA'),0.78,2028),
    ('SSN-VIRGINIA','NAVAL','Virginia Block V','USA',jsonb_build_object('crew',135,'displacement_tons',10200,'speed_kts','25+','range_nm','Unlimited (nuclear)','vls_cells','40 VPM','radar','BYG-1'),0.95,2020),
    ('SSN-ASTUTE','NAVAL','Astute-class','GBR',jsonb_build_object('crew',98,'displacement_tons',7800,'speed_kts','29+','range_nm','Unlimited (nuclear)','vls_cells','— (38 weapons)','radar','Sonar 2076'),0.90,2010),
    ('SSN-SUFFREN','NAVAL','Suffren (Barracuda)','FRA',jsonb_build_object('crew',65,'displacement_tons',5300,'speed_kts','25+','range_nm','Unlimited (nuclear)','vls_cells','— (F21 + MdCN)','radar','—'),0.87,2020),
    ('SSN-YASEN','NAVAL','Yasen-M (Pr. 885M)','RUS',jsonb_build_object('crew',64,'displacement_tons',13800,'speed_kts','31+','range_nm','Unlimited (nuclear)','vls_cells','32 (3M55/3M22)','radar','Irtysh-Amfora'),0.88,2021),
    ('SSBN-COLUMBIA','NAVAL','Columbia-class','USA',jsonb_build_object('crew',155,'displacement_tons',20800,'speed_kts','20+','range_nm','Unlimited (nuclear)','vls_cells','16 Trident II D5LE','radar','—'),0.98,2031),
    ('CVN-FORD','NAVAL','Gerald R. Ford (CVN-78)','USA',jsonb_build_object('crew',4660,'displacement_tons',100000,'speed_kts','30+','range_nm','Unlimited (nuclear)','vls_cells','ESSM + RIM-116','radar','DBR (SPY-3 + SPY-4)'),0.99,2017),
    ('CV-LIAONING','NAVAL','Liaoning (Type 001)','CHN',jsonb_build_object('crew',2000,'displacement_tons',67500,'speed_kts','32','range_nm','3850','vls_cells','HHQ-10','radar','Type 346'),0.72,2012),
    ('CV-FUJIAN','NAVAL','Fujian (Type 003)','CHN',jsonb_build_object('crew','~2500','displacement_tons',80000,'speed_kts','30+','range_nm','—','vls_cells','—','radar','Type 346B'),0.82,2024)
ON CONFLICT (type_code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- MISSILE (Air defense, ballistic, cruise, hypersonic)
-- ---------------------------------------------------------------------------
INSERT INTO equipment_catalog (
    type_code, category, name, origin_country, specs, threat_score, in_service_year
) VALUES
    ('SAM-PATRIOT','MISSILE','MIM-104 Patriot PAC-3 MSE','USA',jsonb_build_object('range_km','150','ceiling_m','24000','missiles_per_battery','16 per launcher','target_types','Aircraft, TBM, cruise missile'),0.90,2015),
    ('SAM-THAAD','MISSILE','THAAD','USA',jsonb_build_object('range_km','200','ceiling_m','150000','missiles_per_battery','48 per battery','target_types','TBM, IRBM exo-atmospheric'),0.92,2008),
    ('SAM-NASAMS','MISSILE','NASAMS 3','NOR',jsonb_build_object('range_km','40','ceiling_m','16000','missiles_per_battery','6 per launcher','target_types','Aircraft, cruise missile, UAV'),0.75,2019),
    ('SAM-IHDP','MISSILE','Iron Dome + David''s Sling','ISR',jsonb_build_object('range_km','70 (DS) / 10 (ID)','ceiling_m','15000','missiles_per_battery','Variable','target_types','Rockets, artillery, cruise missiles, TBM'),0.88,2017),
    ('SAM-ASTER30','MISSILE','SAMP/T Aster 30','FRA',jsonb_build_object('range_km','120','ceiling_m','20000','missiles_per_battery','48 per battery','target_types','Aircraft, TBM, cruise missile'),0.85,2011),
    ('SAM-S400','MISSILE','S-400 Triumf','RUS',jsonb_build_object('range_km','400','ceiling_m','30000','missiles_per_battery','4 × 4 per battery','target_types','Aircraft, cruise missile, TBM'),0.88,2007),
    ('SAM-S300V4','MISSILE','S-300V4 Antey-2500','RUS',jsonb_build_object('range_km','400','ceiling_m','37000','missiles_per_battery','4 per TEL','target_types','TBM, IRBM, aircraft'),0.84,2014),
    ('SAM-S350','MISSILE','S-350 Vityaz','RUS',jsonb_build_object('range_km','120','ceiling_m','30000','missiles_per_battery','12 per launcher','target_types','Aircraft, cruise missile'),0.78,2020),
    ('SAM-BUK3M','MISSILE','Buk-M3 Viking','RUS',jsonb_build_object('range_km','70','ceiling_m','25000','missiles_per_battery','6 per TELAR','target_types','Aircraft, cruise missile, TBM'),0.80,2016),
    ('SAM-PANTSIR','MISSILE','Pantsir-S1M','RUS',jsonb_build_object('range_km','20 (missile) / 4 (gun)','ceiling_m','15000','missiles_per_battery','12 + 2×30mm','target_types','Aircraft, cruise missile, UAV, PGM'),0.72,2019),
    ('SAM-HQ9B','MISSILE','HQ-9B','CHN',jsonb_build_object('range_km','300','ceiling_m','27000','missiles_per_battery','4 per TEL','target_types','Aircraft, cruise missile, TBM'),0.82,2015),
    ('SAM-HQ22','MISSILE','HQ-22','CHN',jsonb_build_object('range_km','170','ceiling_m','27000','missiles_per_battery','4 per TEL','target_types','Aircraft, cruise missile'),0.76,2019),
    ('SAM-CHEOLMAE','MISSILE','Cheolmae-II (M-SAM)','KOR',jsonb_build_object('range_km','40','ceiling_m','15000','missiles_per_battery','6 per launcher','target_types','Aircraft, cruise missile'),0.74,2020),
    ('BM-MINUTEMAN','MISSILE','LGM-30G Minuteman III','USA',jsonb_build_object('range_km','13000','ceiling_m','—','missiles_per_battery','1 per silo','target_types','Strategic ICBM (W87 warhead)'),0.95,1970),
    ('BM-TRIDENT','MISSILE','UGM-133A Trident II D5LE','USA',jsonb_build_object('range_km','12000','ceiling_m','—','missiles_per_battery','4–5 per SSBN tube','target_types','Strategic SLBM (W76-1/W88)'),0.98,1990),
    ('BM-DF41','MISSILE','DF-41 (CSS-20)','CHN',jsonb_build_object('range_km','15000','ceiling_m','—','missiles_per_battery','MIRV 10','target_types','Strategic ICBM, TEL road-mobile'),0.92,2020),
    ('BM-DF21D','MISSILE','DF-21D (CSS-5 Mod 4)','CHN',jsonb_build_object('range_km','1500','ceiling_m','—','missiles_per_battery','1 per TEL','target_types','ASBM (carrier killer)'),0.80,2010),
    ('BM-TOPOL','MISSILE','RS-24 Yars (Topol-M)','RUS',jsonb_build_object('range_km','12000','ceiling_m','—','missiles_per_battery','MIRV 4','target_types','Strategic ICBM, TEL road-mobile'),0.90,2010),
    ('BM-SARMAT','MISSILE','RS-28 Sarmat (Satan II)','RUS',jsonb_build_object('range_km','18000','ceiling_m','—','missiles_per_battery','MIRV 10–15','target_types','Strategic ICBM, silo-based'),0.93,2023),
    ('BM-HWASONG18','MISSILE','Hwasong-18','PRK',jsonb_build_object('range_km','15000','ceiling_m','—','missiles_per_battery','1 per TEL','target_types','Strategic ICBM, solid-fuel'),0.65,2023),
    ('CM-TOMAHAWK','MISSILE','BGM-109 Tomahawk Block V','USA',jsonb_build_object('range_km','1600','ceiling_m','—','missiles_per_battery','Per VLS cell','target_types','Land attack cruise missile'),0.88,2021),
    ('CM-SCALP','MISSILE','SCALP-EG / Storm Shadow','FRA',jsonb_build_object('range_km','560','ceiling_m','—','missiles_per_battery','Per aircraft pylon','target_types','Land attack cruise missile, stealth'),0.82,2003),
    ('CM-KALIBR','MISSILE','3M-14 Kalibr','RUS',jsonb_build_object('range_km','1500–2500','ceiling_m','—','missiles_per_battery','Per VLS cell','target_types','Land attack cruise missile'),0.80,2015),
    ('HGV-DF17','MISSILE','DF-ZF (DF-17 glide vehicle)','CHN',jsonb_build_object('range_km','2500','ceiling_m','—','missiles_per_battery','1 per TEL','target_types','Hypersonic glide vehicle'),0.85,2019),
    ('HGV-AVANGARD','MISSILE','Avangard (Yu-74)','RUS',jsonb_build_object('range_km','6000+','ceiling_m','—','missiles_per_battery','1 per ICBM booster','target_types','Hypersonic glide vehicle'),0.88,2019),
    ('CM-BRAHMOS2','MISSILE','BrahMos-II','IND',jsonb_build_object('range_km','600','ceiling_m','—','missiles_per_battery','Per launcher','target_types','Hypersonic cruise missile'),0.78,2030)
ON CONFLICT (type_code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- ARTILLERY (SPH, MLRS, Mortar)
-- ---------------------------------------------------------------------------
INSERT INTO equipment_catalog (
    type_code, category, name, origin_country, specs, threat_score, in_service_year
) VALUES
    ('SPH-M109A7','ARTILLERY','M109A7 Paladin','USA',jsonb_build_object('caliber_mm','155','range_km','30 (base) / 40 (RAP)','rate_of_fire_rpm','4','crew','4','mobility','Tracked SP'),0.78,2017),
    ('SPH-PZH2000','ARTILLERY','PzH 2000','DEU',jsonb_build_object('caliber_mm','155','range_km','40 (base) / 56 (Vulcano)','rate_of_fire_rpm','9','crew','5','mobility','Tracked SP'),0.88,1998),
    ('SPH-CAESAR2','ARTILLERY','CAESAR Mk 2','FRA',jsonb_build_object('caliber_mm','155','range_km','42 (base) / 50+ (ERFB)','rate_of_fire_rpm','6','crew','4','mobility','Wheeled (8×8) SP'),0.82,2024),
    ('SPH-K9A2','ARTILLERY','K9A2 Thunder','KOR',jsonb_build_object('caliber_mm','155','range_km','40 (base) / 54 (K315 ERM)','rate_of_fire_rpm','6','crew','3','mobility','Tracked SP'),0.85,2023),
    ('SPH-ARCHER','ARTILLERY','Archer FH77BW L52','SWE',jsonb_build_object('caliber_mm','155','range_km','40 (base) / 60 (Excalibur)','rate_of_fire_rpm','9 (burst)','crew','2–4','mobility','Wheeled (6×6) SP'),0.84,2013),
    ('SPH-2S19M2','ARTILLERY','2S19M2 Msta-S','RUS',jsonb_build_object('caliber_mm','152','range_km','29 (base) / 36 (RAP)','rate_of_fire_rpm','8','crew','5','mobility','Tracked SP'),0.72,2013),
    ('SPH-2S35','ARTILLERY','2S35 Koalitsiya-SV','RUS',jsonb_build_object('caliber_mm','152','range_km','40 (base) / 70 (guided)','rate_of_fire_rpm','12','crew','2','mobility','Tracked SP'),0.80,2020),
    ('SPH-PLZ05','ARTILLERY','PLZ-05A','CHN',jsonb_build_object('caliber_mm','155','range_km','39 (base) / 53 (ERFB-BB)','rate_of_fire_rpm','8','crew','4','mobility','Tracked SP'),0.76,2008),
    ('MLRS-HIMARS','ARTILLERY','M142 HIMARS','USA',jsonb_build_object('caliber_mm','227mm / ATACMS / PrSM','range_km','300 (GMLRS) / 500 (PrSM)','rate_of_fire_rpm','6 rkt pod','crew','3','mobility','Wheeled (6×6)'),0.90,2005),
    ('MLRS-M270','ARTILLERY','M270A2 MLRS','USA',jsonb_build_object('caliber_mm','227mm / ATACMS','range_km','300 (GMLRS) / 300 (ATACMS)','rate_of_fire_rpm','12 rkt pod','crew','3','mobility','Tracked'),0.88,2023),
    ('MLRS-BM30','ARTILLERY','BM-30 Smerch (9A52-4)','RUS',jsonb_build_object('caliber_mm','300mm','range_km','90 (base) / 120 (9M542)','rate_of_fire_rpm','12 tube','crew','4','mobility','Wheeled (8×8)'),0.78,2011),
    ('MLRS-BM21','ARTILLERY','BM-21 Grad','RUS',jsonb_build_object('caliber_mm','122mm','range_km','40','rate_of_fire_rpm','40 tube','crew','3','mobility','Wheeled (6×6)'),0.55,1963),
    ('MLRS-PHL03','ARTILLERY','PHL-03A','CHN',jsonb_build_object('caliber_mm','300mm','range_km','130','rate_of_fire_rpm','12 tube','crew','4','mobility','Wheeled (8×8)'),0.76,2004),
    ('MRT-120','ARTILLERY','M120 Mortar (Rifled 120mm)','USA',jsonb_build_object('caliber_mm','120','range_km','7.2','rate_of_fire_rpm','4','crew','4','mobility','Towed'),0.45,1991)
ON CONFLICT (type_code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- IFV / APC
-- ---------------------------------------------------------------------------
INSERT INTO equipment_catalog (
    type_code, category, name, origin_country, specs, threat_score, in_service_year
) VALUES
    ('IFV-M2A3','IFV','M2A3 Bradley','USA',jsonb_build_object('crew_dismounts','3+6','weight_tons',33.6,'speed_kph',61,'armament','25mm M242 + TOW-2B','amphibious',false),0.85,2000),
    ('IFV-PUMA','IFV','Puma','DEU',jsonb_build_object('crew_dismounts','3+6','weight_tons',43.0,'speed_kph',70,'armament','30mm MK 30-2 + Spike LR','amphibious',false),0.88,2015),
    ('IFV-WARRIOR','IFV','Warrior CSP','GBR',jsonb_build_object('crew_dismounts','3+7','weight_tons',28.0,'speed_kph',75,'armament','40mm CTAS','amphibious',false),0.80,2025),
    ('IFV-VBCI','IFV','VBCI 2','FRA',jsonb_build_object('crew_dismounts','3+9','weight_tons',29.0,'speed_kph',100,'armament','25mm M811','amphibious',false),0.78,2015),
    ('IFV-CV90','IFV','CV90 Mk IV','SWE',jsonb_build_object('crew_dismounts','3+8','weight_tons',37.0,'speed_kph',70,'armament','35mm Bushmaster III','amphibious',false),0.86,2018),
    ('IFV-BMP3','IFV','BMP-3','RUS',jsonb_build_object('crew_dismounts','3+7','weight_tons',18.7,'speed_kph',70,'armament','100mm 2A70 + 30mm 2A72','amphibious',true),0.75,1987),
    ('IFV-BMP2M','IFV','BMP-2M Berezhok','RUS',jsonb_build_object('crew_dismounts','3+7','weight_tons',14.3,'speed_kph',65,'armament','30mm 2A42 + Kornet','amphibious',true),0.72,2019),
    ('IFV-ZBD04A','IFV','ZBD-04A','CHN',jsonb_build_object('crew_dismounts','3+7','weight_tons',24.5,'speed_kph',65,'armament','100mm rifled + 30mm auto','amphibious',true),0.73,2016),
    ('IFV-NAMER','IFV','Namer','ISR',jsonb_build_object('crew_dismounts','3+9','weight_tons',60.0,'speed_kph',60,'armament','30mm Mk 44 + Trophy','amphibious',false),0.90,2018),
    ('IFV-K21','IFV','K21','KOR',jsonb_build_object('crew_dismounts','3+9','weight_tons',25.6,'speed_kph',70,'armament','40mm L/70','amphibious',true),0.80,2009),
    ('IFV-LYNX','IFV','KF41 Lynx','DEU',jsonb_build_object('crew_dismounts','3+8','weight_tons',44.0,'speed_kph',65,'armament','35mm Wotan + Spike LR','amphibious',false),0.87,2020),
    ('APC-STRYKER','IFV','Stryker M1126','USA',jsonb_build_object('crew_dismounts','2+9','weight_tons',18.6,'speed_kph',97,'armament','12.7mm M2 or 30mm MCT-30','amphibious',false),0.70,2002),
    ('APC-BOXER','IFV','Boxer CRV','DEU',jsonb_build_object('crew_dismounts','2+8','weight_tons',38.0,'speed_kph',103,'armament','30mm Mk 44 (CRV variant)','amphibious',false),0.82,2011),
    ('APC-PATRIA','IFV','Patria AMV XP','FIN',jsonb_build_object('crew_dismounts','2+10','weight_tons',30.0,'speed_kph',100,'armament','Configurable turret','amphibious',true),0.75,2013),
    ('APC-BTR82A','IFV','BTR-82A','RUS',jsonb_build_object('crew_dismounts','3+7','weight_tons',15.4,'speed_kph',80,'armament','30mm 2A72','amphibious',true),0.60,2013)
ON CONFLICT (type_code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- AIRCRAFT (Fighter / Attack)
-- ---------------------------------------------------------------------------
INSERT INTO equipment_catalog (
    type_code, category, name, origin_country, specs, threat_score, in_service_year
) VALUES
    ('FTR-F35A','AIRCRAFT','F-35A Lightning II','USA',jsonb_build_object('crew_config','1','max_speed_kph',1960,'combat_radius_km',1093,'ceiling_m',15240,'payload_kg',8160,'stealth','yes','generation','5th'),0.95,2015),
    ('FTR-F35B','AIRCRAFT','F-35B Lightning II','USA',jsonb_build_object('crew_config','1','max_speed_kph',1960,'combat_radius_km',935,'ceiling_m',15240,'payload_kg',6800,'stealth','yes','generation','5th'),0.93,2015),
    ('FTR-F22','AIRCRAFT','F-22A Raptor','USA',jsonb_build_object('crew_config','1','max_speed_kph',2410,'combat_radius_km',759,'ceiling_m',19812,'payload_kg',10000,'stealth','yes','generation','5th'),0.97,2005),
    ('FTR-F15EX','AIRCRAFT','F-15EX Eagle II','USA',jsonb_build_object('crew_config','1-2','max_speed_kph',2665,'combat_radius_km',1270,'ceiling_m',19812,'payload_kg',11113,'stealth','no','generation','4.5th'),0.88,2021),
    ('FTR-F16V','AIRCRAFT','F-16V Viper','USA',jsonb_build_object('crew_config','1','max_speed_kph',2120,'combat_radius_km',546,'ceiling_m',15240,'payload_kg',7700,'stealth','no','generation','4th'),0.78,2016),
    ('FTR-FA18EF','AIRCRAFT','F/A-18E/F Super Hornet','USA',jsonb_build_object('crew_config','1-2','max_speed_kph',1915,'combat_radius_km',722,'ceiling_m',15240,'payload_kg',8050,'stealth','no','generation','4.5th'),0.82,2001),
    ('FTR-TYPHOON','AIRCRAFT','Eurofighter Typhoon Tranche 4','GBR',jsonb_build_object('crew_config','1-2','max_speed_kph',2495,'combat_radius_km',1389,'ceiling_m',16764,'payload_kg',9000,'stealth','no','generation','4.5th'),0.86,2020),
    ('FTR-RAFALE','AIRCRAFT','Dassault Rafale F4','FRA',jsonb_build_object('crew_config','1-2','max_speed_kph',1912,'combat_radius_km',1093,'ceiling_m',15235,'payload_kg',9500,'stealth','no','generation','4.5th'),0.87,2023),
    ('FTR-GRIPEN','AIRCRAFT','JAS 39E Gripen','SWE',jsonb_build_object('crew_config','1','max_speed_kph',2204,'combat_radius_km',800,'ceiling_m',15240,'payload_kg',5300,'stealth','no','generation','4.5th'),0.80,2019),
    ('FTR-SU57','AIRCRAFT','Su-57 Felon','RUS',jsonb_build_object('crew_config','1','max_speed_kph',2600,'combat_radius_km',1500,'ceiling_m',20000,'payload_kg',10000,'stealth','yes','generation','5th'),0.85,2020),
    ('FTR-SU35S','AIRCRAFT','Su-35S Flanker-E','RUS',jsonb_build_object('crew_config','1','max_speed_kph',2500,'combat_radius_km',1580,'ceiling_m',18000,'payload_kg',8000,'stealth','no','generation','4++'),0.83,2014),
    ('FTR-SU34','AIRCRAFT','Su-34 Fullback','RUS',jsonb_build_object('crew_config','2','max_speed_kph',1900,'combat_radius_km',1100,'ceiling_m',15000,'payload_kg',12000,'stealth','no','generation','4+'),0.78,2014),
    ('FTR-MIG35','AIRCRAFT','MiG-35 Fulcrum-F','RUS',jsonb_build_object('crew_config','1-2','max_speed_kph',2400,'combat_radius_km',1000,'ceiling_m',17500,'payload_kg',7000,'stealth','no','generation','4++'),0.75,2019),
    ('FTR-J20','AIRCRAFT','J-20 Mighty Dragon','CHN',jsonb_build_object('crew_config','1','max_speed_kph',2100,'combat_radius_km',1100,'ceiling_m',20000,'payload_kg',8000,'stealth','yes','generation','5th'),0.84,2017),
    ('FTR-J16','AIRCRAFT','J-16','CHN',jsonb_build_object('crew_config','2','max_speed_kph',2400,'combat_radius_km',1500,'ceiling_m',17000,'payload_kg',12000,'stealth','no','generation','4.5th'),0.79,2015),
    ('FTR-J10C','AIRCRAFT','J-10C Vigorous Dragon','CHN',jsonb_build_object('crew_config','1','max_speed_kph',2200,'combat_radius_km',550,'ceiling_m',18000,'payload_kg',6000,'stealth','no','generation','4th'),0.73,2018),
    ('FTR-KF21','AIRCRAFT','KF-21 Boramae','KOR',jsonb_build_object('crew_config','1-2','max_speed_kph',1960,'combat_radius_km',800,'ceiling_m',16800,'payload_kg',7700,'stealth','reduced','generation','4.5th'),0.80,2026),
    ('FTR-TEJAS2','AIRCRAFT','HAL Tejas Mk 2','IND',jsonb_build_object('crew_config','1','max_speed_kph',1850,'combat_radius_km',500,'ceiling_m',15250,'payload_kg',5500,'stealth','no','generation','4th'),0.68,2028),
    ('ATK-A10C','AIRCRAFT','A-10C Thunderbolt II','USA',jsonb_build_object('crew_config','1','max_speed_kph',706,'combat_radius_km',460,'ceiling_m',13636,'payload_kg',7260,'stealth','no','generation',NULL),0.75,2007),
    ('ATK-SU25SM3','AIRCRAFT','Su-25SM3 Frogfoot','RUS',jsonb_build_object('crew_config','1','max_speed_kph',975,'combat_radius_km',375,'ceiling_m',10000,'payload_kg',4400,'stealth','no','generation',NULL),0.65,2017)
ON CONFLICT (type_code) DO NOTHING;
