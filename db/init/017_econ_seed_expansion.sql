-- =============================================================================
-- 017_econ_seed_expansion.sql
-- Economic Warfare seed expansion (countries, sanctions, trade routes, indicators)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Country backfill for expanded econ seed coverage
-- ---------------------------------------------------------------------------
INSERT INTO countries (
    code, name, region, alliance_codes, gdp_usd, defense_budget_usd,
    population, area_km2, iso2, flag_emoji
) VALUES
    ('AFG', 'Afghanistan', 'South Asia', ARRAY[]::TEXT[], NULL, NULL, NULL, NULL, 'AF', '🇦🇫'),
    ('BLR', 'Belarus', 'Eastern Europe', ARRAY['CSTO']::TEXT[], NULL, NULL, NULL, NULL, 'BY', '🇧🇾'),
    ('CAF', 'Central African Republic', 'Central Africa', ARRAY[]::TEXT[], NULL, NULL, NULL, NULL, 'CF', '🇨🇫'),
    ('COD', 'Democratic Republic of the Congo', 'Central Africa', ARRAY[]::TEXT[], NULL, NULL, NULL, NULL, 'CD', '🇨🇩'),
    ('CUB', 'Cuba', 'Caribbean', ARRAY[]::TEXT[], NULL, NULL, NULL, NULL, 'CU', '🇨🇺'),
    ('ERI', 'Eritrea', 'East Africa', ARRAY[]::TEXT[], NULL, NULL, NULL, NULL, 'ER', '🇪🇷'),
    ('IRQ', 'Iraq', 'Middle East', ARRAY[]::TEXT[], NULL, NULL, NULL, NULL, 'IQ', '🇮🇶'),
    ('LBN', 'Lebanon', 'Middle East', ARRAY[]::TEXT[], NULL, NULL, NULL, NULL, 'LB', '🇱🇧'),
    ('LBY', 'Libya', 'North Africa', ARRAY[]::TEXT[], NULL, NULL, NULL, NULL, 'LY', '🇱🇾'),
    ('MLI', 'Mali', 'West Africa', ARRAY[]::TEXT[], NULL, NULL, NULL, NULL, 'ML', '🇲🇱'),
    ('MMR', 'Myanmar', 'Southeast Asia', ARRAY[]::TEXT[], NULL, NULL, NULL, NULL, 'MM', '🇲🇲'),
    ('NIC', 'Nicaragua', 'Central America', ARRAY[]::TEXT[], NULL, NULL, NULL, NULL, 'NI', '🇳🇮'),
    ('SDN', 'Sudan', 'North Africa', ARRAY[]::TEXT[], NULL, NULL, NULL, NULL, 'SD', '🇸🇩'),
    ('SOM', 'Somalia', 'East Africa', ARRAY[]::TEXT[], NULL, NULL, NULL, NULL, 'SO', '🇸🇴'),
    ('SSD', 'South Sudan', 'East Africa', ARRAY[]::TEXT[], NULL, NULL, NULL, NULL, 'SS', '🇸🇸'),
    ('SYR', 'Syria', 'Middle East', ARRAY[]::TEXT[], NULL, NULL, NULL, NULL, 'SY', '🇸🇾'),
    ('YEM', 'Yemen', 'Middle East', ARRAY[]::TEXT[], NULL, NULL, NULL, NULL, 'YE', '🇾🇪'),
    ('ZWE', 'Zimbabwe', 'Southern Africa', ARRAY[]::TEXT[], NULL, NULL, NULL, NULL, 'ZW', '🇿🇼')
ON CONFLICT (code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Expanded sanctions
-- ---------------------------------------------------------------------------
INSERT INTO econ_sanction_targets (
    id, name, country_code, target_type, sanction_type, status,
    imposing_parties, effective_date, annual_gdp_impact_pct, notes, classification
) VALUES
    ('e1700000-0000-0000-0000-000000000001', 'Cuba — Comprehensive Trade Embargo', 'CUB', 'COUNTRY', 'TRADE_EMBARGO', 'ACTIVE', '["USA"]', '1962-02-07', 5.0, 'Full US embargo since 1962; limited humanitarian exceptions.', 'UNCLASS'),
    ('e1700000-0000-0000-0000-000000000002', 'Syria — Comprehensive Sanctions Regime', 'SYR', 'COUNTRY', 'TRADE_EMBARGO', 'ACTIVE', '["USA","EU"]', '2011-08-18', 8.5, 'Broad restrictions on energy, finance, and investment; partial EU/UK easing in 2025 for humanitarian purposes.', 'UNCLASS'),
    ('e1700000-0000-0000-0000-000000000003', 'Myanmar — Post-Coup Sectoral Measures', 'MMR', 'COUNTRY', 'SECTORAL', 'ACTIVE', '["USA","EU","UK"]', '2021-02-01', 3.2, 'Post-coup military regime; energy, mining, and financial sector restrictions.', 'UNCLASS'),
    ('e1700000-0000-0000-0000-000000000004', 'Occupied Crimea/Donetsk/Luhansk Restrictions', 'UKR', 'COUNTRY', 'TRADE_EMBARGO', 'ACTIVE', '["USA","EU"]', '2014-03-17', NULL, 'Embargo on business and investment in occupied Crimea, Donetsk, and Luhansk regions.', 'UNCLASS'),
    ('e1700000-0000-0000-0000-000000000005', 'Sudan — Targeted Freeze Program', 'SDN', 'COUNTRY', 'ASSET_FREEZE', 'ACTIVE', '["USA","EU","UN"]', '1997-11-03', 2.8, 'Targeted sanctions on military officials and entities.', 'UNCLASS'),
    ('e1700000-0000-0000-0000-000000000006', 'South Sudan — UN Arms Embargo', 'SSD', 'COUNTRY', 'ARMS_EMBARGO', 'ACTIVE', '["UN"]', '2018-07-13', 1.5, 'UN arms embargo with targeted freezes on officials.', 'UNCLASS'),
    ('e1700000-0000-0000-0000-000000000007', 'Somalia — Long-standing Arms Embargo', 'SOM', 'COUNTRY', 'ARMS_EMBARGO', 'ACTIVE', '["UN"]', '1992-01-23', 1.0, 'UN arms embargo with Al-Shabaab-targeted restrictions.', 'UNCLASS'),
    ('e1700000-0000-0000-0000-000000000008', 'Libya — Arms and Asset Restrictions', 'LBY', 'COUNTRY', 'ARMS_EMBARGO', 'ACTIVE', '["UN","EU"]', '2011-02-26', 3.5, 'UN arms embargo plus targeted asset freezes and oil-sector restrictions.', 'UNCLASS'),
    ('e1700000-0000-0000-0000-000000000009', 'Yemen — Houthi-Linked Sanctions', 'YEM', 'COUNTRY', 'ASSET_FREEZE', 'ACTIVE', '["USA","UN"]', '2014-11-07', 2.0, 'Targeted sanctions with humanitarian exemptions.', 'UNCLASS'),
    ('e1700000-0000-0000-0000-000000000010', 'Zimbabwe — Travel and Targeted Measures', 'ZWE', 'COUNTRY', 'TRAVEL_BAN', 'ACTIVE', '["USA","EU"]', '2003-02-18', 1.8, 'Targeted sanctions on officials; mining and finance constraints.', 'UNCLASS'),
    ('e1700000-0000-0000-0000-000000000011', 'Central African Republic — Arms Controls', 'CAF', 'COUNTRY', 'ARMS_EMBARGO', 'ACTIVE', '["UN"]', '2013-12-05', 0.8, 'UN arms embargo and travel bans on armed-group leaders.', 'UNCLASS'),
    ('e1700000-0000-0000-0000-000000000012', 'DR Congo — Armed Group Measures', 'COD', 'COUNTRY', 'ARMS_EMBARGO', 'ACTIVE', '["UN","EU"]', '2003-07-28', 1.2, 'Arms controls and targeted sanctions on armed groups.', 'UNCLASS'),
    ('e1700000-0000-0000-0000-000000000013', 'Ethiopia — Conflict-linked Designations', 'ETH', 'COUNTRY', 'ASSET_FREEZE', 'ACTIVE', '["USA"]', '2021-09-17', 1.0, 'Targeted post-Tigray conflict sanctions.', 'UNCLASS'),
    ('e1700000-0000-0000-0000-000000000014', 'Nicaragua — Regime Targeting Program', 'NIC', 'COUNTRY', 'ASSET_FREEZE', 'ACTIVE', '["USA","EU","Canada"]', '2018-11-27', 1.5, 'Targeted sanctions on Ortega-aligned officials and entities.', 'UNCLASS'),
    ('e1700000-0000-0000-0000-000000000015', 'Mali — Junta-related Sectoral Measures', 'MLI', 'COUNTRY', 'SECTORAL', 'ACTIVE', '["EU"]', '2022-01-10', 1.8, 'EU measures aligned with regional ECOWAS restrictions.', 'UNCLASS'),
    ('e1700000-0000-0000-0000-000000000016', 'Lebanon — Hezbollah-linked Measures', 'LBN', 'COUNTRY', 'ASSET_FREEZE', 'ACTIVE', '["USA"]', '2007-08-01', 0.5, 'Hezbollah-targeted sanctions and financial restrictions.', 'UNCLASS'),
    ('e1700000-0000-0000-0000-000000000017', 'Afghanistan — Taliban Asset Freeze', 'AFG', 'COUNTRY', 'ASSET_FREEZE', 'ACTIVE', '["USA","UN"]', '2021-08-15', 4.0, 'Taliban government-linked freezes including reserve constraints.', 'UNCLASS'),
    ('e1700000-0000-0000-0000-000000000018', 'Iraq — Residual UN Sectoral Measures', 'IRQ', 'COUNTRY', 'SECTORAL', 'ACTIVE', '["UN"]', '2003-05-22', 0.3, 'Residual WMD-related measures; most historic sanctions lifted.', 'UNCLASS'),
    ('e1700000-0000-0000-0000-000000000019', 'Eritrea — Historic Arms Embargo Legacy', 'ERI', 'COUNTRY', 'ARMS_EMBARGO', 'SUSPENDED', '["UN"]', '2009-12-23', 1.0, 'UN arms embargo lifted in 2018; some targeted sanctions remained externally.', 'UNCLASS')
ON CONFLICT (id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Expanded trade routes
-- ---------------------------------------------------------------------------
INSERT INTO econ_trade_routes (
    id, origin_country, destination_country, commodity,
    annual_value_usd, dependency_level, is_disrupted, disruption_cause, classification
) VALUES
    ('e1700000-1000-0000-0000-000000000001', 'CUB', 'EUR', 'sugar_tobacco', 800000000, 'MEDIUM', TRUE, 'US embargo restricts re-export pathways; limited EU trade access.', 'UNCLASS'),
    ('e1700000-1000-0000-0000-000000000002', 'SYR', 'TUR', 'crude_oil', 2000000000, 'HIGH', TRUE, 'Civil war disruption, sanctions pressure, and pipeline constraints.', 'UNCLASS'),
    ('e1700000-1000-0000-0000-000000000003', 'MMR', 'CHN', 'natural_gas', 3500000000, 'HIGH', FALSE, NULL, 'UNCLASS'),
    ('e1700000-1000-0000-0000-000000000004', 'MMR', 'CHN', 'jade_gemstones', 15000000000, 'CRITICAL', FALSE, 'Largely unregulated revenue stream linked to military networks.', 'UNCLASS'),
    ('e1700000-1000-0000-0000-000000000005', 'IRN', 'CHN', 'crude_oil', 25000000000, 'CRITICAL', FALSE, 'Sanctions-evasion logistics including ship-to-ship transfer behavior.', 'UNCLASS'),
    ('e1700000-1000-0000-0000-000000000006', 'IRN', 'IND', 'crude_oil', 12000000000, 'HIGH', TRUE, 'US secondary sanctions create financing and insurance pressure.', 'UNCLASS'),
    ('e1700000-1000-0000-0000-000000000007', 'RUS', 'IND', 'crude_oil', 45000000000, 'HIGH', FALSE, 'Discounted bilateral oil trade expansion since 2022.', 'UNCLASS'),
    ('e1700000-1000-0000-0000-000000000008', 'RUS', 'CHN', 'crude_oil', 60000000000, 'HIGH', FALSE, 'Pipeline and seaborne exports via diversified delivery channels.', 'UNCLASS'),
    ('e1700000-1000-0000-0000-000000000009', 'UKR', 'EUR', 'grain_cereals', 12000000000, 'HIGH', TRUE, 'Black Sea access instability and corridor negotiation risk.', 'UNCLASS'),
    ('e1700000-1000-0000-0000-000000000010', 'LBY', 'EUR', 'crude_oil', 20000000000, 'MEDIUM', TRUE, 'Civil conflict and terminal outages disrupt export continuity.', 'UNCLASS'),
    ('e1700000-1000-0000-0000-000000000011', 'SDN', 'ARE', 'gold', 4500000000, 'HIGH', TRUE, 'Civil war fragmentation and smuggling network dependence.', 'UNCLASS'),
    ('e1700000-1000-0000-0000-000000000012', 'AFG', 'PAK', 'coal_minerals', 1400000000, 'MEDIUM', FALSE, NULL, 'UNCLASS'),
    ('e1700000-1000-0000-0000-000000000013', 'PRK', 'CHN', 'coal_iron_ore', 2000000000, 'CRITICAL', TRUE, 'UN sanctions and maritime interdiction pressure; smuggling persists.', 'UNCLASS'),
    ('e1700000-1000-0000-0000-000000000014', 'VEN', 'CHN', 'crude_oil', 5000000000, 'HIGH', TRUE, 'US sanctions and discounted cargo pricing constraints.', 'UNCLASS'),
    ('e1700000-1000-0000-0000-000000000015', 'COD', 'CHN', 'cobalt_coltan', 8000000000, 'CRITICAL', FALSE, 'Critical battery supply-chain dependency.', 'UNCLASS')
ON CONFLICT (id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Expanded indicators (source year snapshots)
-- ---------------------------------------------------------------------------
INSERT INTO econ_indicators (
    id, country_code, indicator_name, value, unit, year, source, classification
) VALUES
    ('e1700000-2000-0000-0000-000000000001', 'RUS', 'GDP_GROWTH_RATE', -2.10, 'percent', 2023, 'IMF', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000002', 'RUS', 'INFLATION', 7.40, 'percent', 2023, 'IMF', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000003', 'RUS', 'UNEMPLOYMENT', 3.90, 'percent', 2023, 'IMF', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000004', 'IRN', 'GDP_GROWTH_RATE', 1.40, 'percent', 2023, 'IMF', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000005', 'IRN', 'INFLATION', 44.60, 'percent', 2023, 'IMF', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000006', 'PRK', 'GDP_GROWTH_RATE', -4.50, 'percent', 2022, 'Bank of Korea', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000007', 'CHN', 'GDP_GROWTH_RATE', 5.20, 'percent', 2023, 'NBS China', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000008', 'CHN', 'INFLATION', 0.20, 'percent', 2023, 'NBS China', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000009', 'USA', 'GDP_GROWTH_RATE', 2.50, 'percent', 2023, 'BEA/BLS', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000010', 'USA', 'INFLATION', 3.40, 'percent', 2023, 'BEA/BLS', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000011', 'CUB', 'GDP_GROWTH_RATE', 1.80, 'percent', 2023, 'ONEI Cuba / IMF', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000012', 'CUB', 'INFLATION', 39.00, 'percent', 2023, 'ONEI Cuba / IMF', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000013', 'CUB', 'UNEMPLOYMENT', 1.40, 'percent', 2023, 'ONEI Cuba / IMF', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000014', 'SYR', 'GDP_GROWTH_RATE', -3.20, 'percent', 2023, 'World Bank est.', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000015', 'SYR', 'INFLATION', 115.00, 'percent', 2023, 'World Bank est.', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000016', 'SYR', 'UNEMPLOYMENT', 50.00, 'percent', 2023, 'World Bank est.', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000017', 'MMR', 'GDP_GROWTH_RATE', 2.50, 'percent', 2023, 'World Bank', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000018', 'MMR', 'INFLATION', 14.20, 'percent', 2023, 'World Bank', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000019', 'MMR', 'UNEMPLOYMENT', 2.20, 'percent', 2023, 'World Bank', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000020', 'SDN', 'GDP_GROWTH_RATE', -12.00, 'percent', 2023, 'IMF / World Bank', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000021', 'SDN', 'INFLATION', 256.00, 'percent', 2023, 'IMF / World Bank', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000022', 'SDN', 'UNEMPLOYMENT', 28.00, 'percent', 2023, 'IMF / World Bank', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000023', 'VEN', 'GDP_GROWTH_RATE', 4.00, 'percent', 2023, 'IMF', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000024', 'VEN', 'INFLATION', 190.00, 'percent', 2023, 'IMF', 'UNCLASS'),
    ('e1700000-2000-0000-0000-000000000025', 'VEN', 'UNEMPLOYMENT', 6.40, 'percent', 2023, 'IMF', 'UNCLASS')
ON CONFLICT (id) DO NOTHING;
