-- =============================================================================
-- AGD Seed Data — Top 50 Nations by Military Power
-- Source: GlobalFirepower Index / SIPRI (open/unclassified data only)
-- Classification: UNCLASS
-- =============================================================================

-- Countries (ISO 3166-1 alpha-3, approximate defense budgets in USD)
INSERT INTO countries (code, name, region, alliance_codes, gdp_usd, defense_budget_usd, population, area_km2, iso2, flag_emoji) VALUES
-- Major powers
('USA', 'United States',         'North America',  ARRAY['NATO','QUAD','AUKUS','FPDA'],              27360000000000, 886000000000, 331000000, 9834000, 'US', '🇺🇸'),
('CHN', 'China',                  'East Asia',      ARRAY['SCO'],                                     18530000000000, 296000000000, 1412000000, 9597000, 'CN', '🇨🇳'),
('RUS', 'Russia',                 'Eastern Europe', ARRAY['CSTO','SCO'],                              1862000000000, 109000000000, 144000000, 17098000, 'RU', '🇷🇺'),
('IND', 'India',                  'South Asia',     ARRAY['QUAD','SCO'],                              3730000000000,  75000000000, 1380000000, 3287000, 'IN', '🇮🇳'),
('GBR', 'United Kingdom',         'Western Europe', ARRAY['NATO','AUKUS','FPDA','FVEY'],              3079000000000,  74000000000,  67000000, 243000, 'GB', '🇬🇧'),
('FRA', 'France',                 'Western Europe', ARRAY['NATO'],                                    2924000000000,  57000000000,  68000000, 552000, 'FR', '🇫🇷'),
('DEU', 'Germany',                'Western Europe', ARRAY['NATO'],                                    4456000000000,  52000000000,  84000000, 357000, 'DE', '🇩🇪'),
('JPN', 'Japan',                  'East Asia',      ARRAY['QUAD'],                                    4230000000000,  51000000000, 126000000, 378000, 'JP', '🇯🇵'),
('SAU', 'Saudi Arabia',           'Middle East',    ARRAY[]::TEXT[],                                  1069000000000,  75000000000,  35000000, 2150000, 'SA', '🇸🇦'),
('KOR', 'South Korea',            'East Asia',      ARRAY[]::TEXT[],                                  1710000000000,  46000000000,  52000000, 100000, 'KR', '🇰🇷'),
-- NATO / Western allies
('ITA', 'Italy',                  'Southern Europe',ARRAY['NATO'],                                    2170000000000,  35000000000,  60000000, 301000, 'IT', '🇮🇹'),
('AUS', 'Australia',              'Oceania',        ARRAY['QUAD','AUKUS','FPDA','FVEY'],               1530000000000,  32000000000,  25000000, 7688000, 'AU', '🇦🇺'),
('CAN', 'Canada',                 'North America',  ARRAY['NATO','FVEY'],                              2140000000000,  27000000000,  38000000, 9985000, 'CA', '🇨🇦'),
('TUR', 'Turkey',                 'Eurasia',        ARRAY['NATO'],                                    1108000000000,  22000000000,  84000000, 784000, 'TR', '🇹🇷'),
('ESP', 'Spain',                  'Southern Europe',ARRAY['NATO'],                                    1583000000000,  19000000000,  47000000, 506000, 'ES', '🇪🇸'),
('POL', 'Poland',                 'Eastern Europe', ARRAY['NATO'],                                     748000000000,  35000000000,  38000000, 313000, 'PL', '🇵🇱'),
('NLD', 'Netherlands',            'Western Europe', ARRAY['NATO'],                                    1118000000000,  18000000000,  17000000,  42000, 'NL', '🇳🇱'),
('NOR', 'Norway',                 'Northern Europe',ARRAY['NATO'],                                     546000000000,   8000000000,   5000000, 385000, 'NO', '🇳🇴'),
('SWE', 'Sweden',                 'Northern Europe',ARRAY['NATO'],                                     585000000000,   9000000000,  10000000, 450000, 'SE', '🇸🇪'),
('GRC', 'Greece',                 'Southern Europe',ARRAY['NATO'],                                     247000000000,   8000000000,  11000000, 132000, 'GR', '🇬🇷'),
-- Middle East / Africa
('ISR', 'Israel',                 'Middle East',    ARRAY[]::TEXT[],                                   564000000000,  24000000000,   9000000,  22000, 'IL', '🇮🇱'),
('IRN', 'Iran',                   'Middle East',    ARRAY[]::TEXT[],                                   411000000000,  10000000000,  87000000, 1648000, 'IR', '🇮🇷'),
('EGY', 'Egypt',                  'North Africa',   ARRAY[]::TEXT[],                                   476000000000,   5000000000, 104000000, 1002000, 'EG', '🇪🇬'),
('ARE', 'United Arab Emirates',   'Middle East',    ARRAY[]::TEXT[],                                   498000000000,  19000000000,  10000000,  84000, 'AE', '🇦🇪'),
('PAK', 'Pakistan',               'South Asia',     ARRAY['SCO'],                                      338000000000,  10000000000, 231000000, 881000, 'PK', '🇵🇰'),
-- Asia
('PRK', 'North Korea',            'East Asia',      ARRAY[]::TEXT[],                                    18000000000,   4000000000,  26000000, 120000, 'KP', '🇰🇵'),
('TWN', 'Taiwan',                 'East Asia',      ARRAY[]::TEXT[],                                   800000000000,  19000000000,  24000000,  36000, 'TW', '🇹🇼'),
('VNM', 'Vietnam',                'Southeast Asia', ARRAY[]::TEXT[],                                   449000000000,   6000000000,  97000000, 331000, 'VN', '🇻🇳'),
('THA', 'Thailand',               'Southeast Asia', ARRAY[]::TEXT[],                                   544000000000,   7000000000,  70000000, 513000, 'TH', '🇹🇭'),
('IDN', 'Indonesia',              'Southeast Asia', ARRAY[]::TEXT[],                                  1419000000000,   9000000000, 277000000, 1905000, 'ID', '🇮🇩'),
('MYS', 'Malaysia',               'Southeast Asia', ARRAY['FPDA'],                                     430000000000,   4000000000,  33000000, 330000, 'MY', '🇲🇾'),
('SGP', 'Singapore',              'Southeast Asia', ARRAY['FPDA'],                                     501000000000,  12000000000,   6000000,   1000, 'SG', '🇸🇬'),
('PHL', 'Philippines',            'Southeast Asia', ARRAY[]::TEXT[],                                   471000000000,   4000000000, 114000000, 300000, 'PH', '🇵🇭'),
-- Eastern Europe / Former Soviet
('UKR', 'Ukraine',                'Eastern Europe', ARRAY[]::TEXT[],                                   176000000000,  65000000000,  44000000, 604000, 'UA', '🇺🇦'),
('AZE', 'Azerbaijan',             'Caucasus',       ARRAY[]::TEXT[],                                    79000000000,   3000000000,  10000000,  87000, 'AZ', '🇦🇿'),
('KAZ', 'Kazakhstan',             'Central Asia',   ARRAY['CSTO','SCO'],                               261000000000,   2000000000,  19000000, 2725000, 'KZ', '🇰🇿'),
-- Latin America
('BRA', 'Brazil',                 'South America',  ARRAY[]::TEXT[],                                  2126000000000,  19000000000, 215000000, 8516000, 'BR', '🇧🇷'),
('MEX', 'Mexico',                 'North America',  ARRAY[]::TEXT[],                                  1322000000000,   7000000000, 130000000, 1964000, 'MX', '🇲🇽'),
('ARG', 'Argentina',              'South America',  ARRAY[]::TEXT[],                                   640000000000,   2000000000,  45000000, 2780000, 'AR', '🇦🇷'),
('COL', 'Colombia',               'South America',  ARRAY[]::TEXT[],                                   363000000000,   4000000000,  51000000, 1142000, 'CO', '🇨🇴'),
('CHL', 'Chile',                  'South America',  ARRAY[]::TEXT[],                                   319000000000,   5000000000,  19000000, 756000, 'CL', '🇨🇱'),
-- Africa
('ZAF', 'South Africa',           'Southern Africa',ARRAY[]::TEXT[],                                   405000000000,   3000000000,  60000000, 1221000, 'ZA', '🇿🇦'),
('NGA', 'Nigeria',                'West Africa',    ARRAY[]::TEXT[],                                   477000000000,   2000000000, 218000000, 924000, 'NG', '🇳🇬'),
('ETH', 'Ethiopia',               'East Africa',    ARRAY[]::TEXT[],                                   155000000000,   1000000000, 126000000, 1104000, 'ET', '🇪🇹'),
-- Other significant
('BEL', 'Belgium',                'Western Europe', ARRAY['NATO'],                                     631000000000,   7000000000,  11000000,  31000, 'BE', '🇧🇪'),
('DNK', 'Denmark',                'Northern Europe',ARRAY['NATO'],                                     406000000000,   6000000000,   6000000,  43000, 'DK', '🇩🇰'),
('FIN', 'Finland',                'Northern Europe',ARRAY['NATO'],                                     309000000000,   5000000000,   6000000, 338000, 'FI', '🇫🇮'),
('PRT', 'Portugal',               'Southern Europe',ARRAY['NATO'],                                     272000000000,   4000000000,  10000000,  92000, 'PT', '🇵🇹'),
('CZE', 'Czech Republic',         'Central Europe', ARRAY['NATO'],                                     336000000000,   4000000000,  11000000,  79000, 'CZ', '🇨🇿'),
('ROU', 'Romania',                'Eastern Europe', ARRAY['NATO'],                                     350000000000,   6000000000,  19000000, 238000, 'RO', '🇷🇴')
ON CONFLICT (code) DO NOTHING;
