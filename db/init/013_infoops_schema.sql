-- =============================================================================
-- 013_infoops_schema.sql
-- Information Operations / Disinformation Tracking schema
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Narrative Threats
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS infoops_narrative_threats (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title               text NOT NULL,
    description         text,
    origin_country      char(3),
    target_countries    jsonb NOT NULL DEFAULT '[]',
    platforms           jsonb NOT NULL DEFAULT '[]',
    status              text NOT NULL DEFAULT 'ACTIVE',
    threat_level        text NOT NULL DEFAULT 'MEDIUM',
    spread_velocity     numeric(4,3) NOT NULL DEFAULT 0.500,
    reach_estimate      bigint NOT NULL DEFAULT 0,
    key_claims          jsonb NOT NULL DEFAULT '[]',
    counter_narratives  jsonb NOT NULL DEFAULT '[]',
    first_detected      timestamptz NOT NULL DEFAULT now(),
    last_updated        timestamptz NOT NULL DEFAULT now(),
    classification      text NOT NULL DEFAULT 'UNCLASS',
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Influence Campaigns
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS infoops_influence_campaigns (
    id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name                    text NOT NULL,
    description             text,
    attributed_actor        text,
    attribution_confidence  text NOT NULL DEFAULT 'UNATTRIBUTED',
    sponsoring_state        char(3),
    target_countries        jsonb NOT NULL DEFAULT '[]',
    target_demographics     jsonb NOT NULL DEFAULT '[]',
    platforms               jsonb NOT NULL DEFAULT '[]',
    status                  text NOT NULL DEFAULT 'UNCONFIRMED',
    campaign_objectives     jsonb NOT NULL DEFAULT '[]',
    estimated_budget_usd    bigint,
    start_date              date,
    end_date                date,
    linked_narrative_ids    jsonb NOT NULL DEFAULT '[]',
    classification          text NOT NULL DEFAULT 'UNCLASS',
    created_at              timestamptz NOT NULL DEFAULT now(),
    updated_at              timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Disinformation Indicators
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS infoops_disinformation_indicators (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    indicator_type      text NOT NULL,
    title               text NOT NULL,
    description         text,
    source_url          text,
    platform            text NOT NULL,
    detected_at         timestamptz NOT NULL DEFAULT now(),
    confidence_score    numeric(4,3) NOT NULL DEFAULT 0.500,
    linked_campaign_id  uuid,
    linked_narrative_id uuid,
    is_verified         boolean NOT NULL DEFAULT false,
    classification      text NOT NULL DEFAULT 'UNCLASS',
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Attribution Assessments
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS infoops_attribution_assessments (
    id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    subject               text NOT NULL,
    attributed_to         text NOT NULL,
    confidence            text NOT NULL DEFAULT 'LOW',
    evidence_summary      text,
    supporting_indicators jsonb NOT NULL DEFAULT '[]',
    dissenting_evidence   jsonb NOT NULL DEFAULT '[]',
    analyst_id            text,
    classification        text NOT NULL DEFAULT 'UNCLASS',
    created_at            timestamptz NOT NULL DEFAULT now(),
    updated_at            timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Seed data
-- ---------------------------------------------------------------------------

-- Narrative threats
INSERT INTO infoops_narrative_threats (
    id, title, description, origin_country, target_countries, platforms,
    status, threat_level, spread_velocity, reach_estimate,
    key_claims, counter_narratives, first_detected, last_updated, classification
) VALUES
(
    'a1000000-0000-0000-0000-000000000001',
    'Russian Energy Security FUD',
    'Coordinated campaign claiming European energy infrastructure is unreliable without Russian gas, designed to undermine EU sanctions resolve.',
    'RUS',
    '["DEU","FRA","POL","ITA","NLD"]',
    '["STATE_MEDIA","SOCIAL_MEDIA","NEWS_OUTLET"]',
    'ACTIVE', 'HIGH', 0.720, 12000000,
    '["EU energy policy is failing citizens","Winter energy shortages are imminent","Russian gas is indispensable for European stability"]',
    '["EU storage levels are at record highs","Diversification of energy sources is progressing","Renewables filling the supply gap"]',
    '2022-03-01T00:00:00Z', now(), 'UNCLASS'
),
(
    'a1000000-0000-0000-0000-000000000002',
    'Taiwan Invasion Justification Narrative',
    'Narrative pre-seeding public opinion to frame a potential Taiwan invasion as a legitimate reunification, framing resistance as illegal separatism.',
    'CHN',
    '["TWN","USA","JPN","AUS","GBR"]',
    '["STATE_MEDIA","SOCIAL_MEDIA","VIDEO_PLATFORM","FORUM"]',
    'ACTIVE', 'CRITICAL', 0.850, 35000000,
    '["Taiwan is an inalienable part of China","Separatist forces threaten regional stability","US interference is the root cause of tensions"]',
    '["Taiwan is a self-governing democracy","Cross-strait stability requires peaceful dialogue","International law supports self-determination"]',
    '2023-06-15T00:00:00Z', now(), 'UNCLASS'
),
(
    'a1000000-0000-0000-0000-000000000003',
    'NATO Expansion Destabilization',
    'Narrative asserting NATO expansion is an existential threat to Russian security, justifying aggressive posturing and undermining alliance cohesion.',
    'RUS',
    '["USA","GBR","DEU","FRA","POL"]',
    '["STATE_MEDIA","NEWS_OUTLET","MESSAGING_APP","BLOG"]',
    'ACTIVE', 'HIGH', 0.650, 8500000,
    '["NATO expansion broke promises made to Russia","Alliance is an offensive instrument","Eastern European members are pawns of US imperialism"]',
    '["NATO is a defensive alliance","No formal commitments were made regarding eastward expansion","Alliance members joined voluntarily"]',
    '2021-11-01T00:00:00Z', now(), 'UNCLASS'
)
ON CONFLICT (id) DO NOTHING;

-- Influence campaigns
INSERT INTO infoops_influence_campaigns (
    id, name, description, attributed_actor, attribution_confidence,
    sponsoring_state, target_countries, target_demographics, platforms,
    status, campaign_objectives, estimated_budget_usd,
    linked_narrative_ids, classification
) VALUES
(
    'b1000000-0000-0000-0000-000000000001',
    'Secondary Infektion',
    'Long-running Russian influence operation using fabricated documents and coordinated inauthentic behaviour to discredit Western institutions.',
    'GRU / FSB',
    'HIGH',
    'RUS',
    '["DEU","FRA","GBR","USA","UKR"]',
    '["populist voters","journalists","policy researchers"]',
    '["SOCIAL_MEDIA","NEWS_OUTLET","BLOG","FORUM"]',
    'ACTIVE',
    '["Discredit NATO","Undermine EU unity","Amplify anti-immigrant sentiment","Support far-right movements"]',
    15000000,
    '["a1000000-0000-0000-0000-000000000001","a1000000-0000-0000-0000-000000000003"]',
    'UNCLASS'
),
(
    'b1000000-0000-0000-0000-000000000002',
    'Sharp Power Coalition',
    'Chinese influence operation targeting Pacific-rim academic and media institutions to shape narratives around Taiwan and South China Sea disputes.',
    'PLA Strategic Support Force',
    'MEDIUM',
    'CHN',
    '["TWN","AUS","NZL","USA","JPN"]',
    '["academics","students","think-tank researchers","diaspora communities"]',
    '["SOCIAL_MEDIA","NEWS_OUTLET","VIDEO_PLATFORM","STATE_MEDIA"]',
    'ACTIVE',
    '["Legitimise Taiwan reunification","Discredit US Indo-Pacific strategy","Cultivate pro-Beijing academics","Suppress critical journalism"]',
    28000000,
    '["a1000000-0000-0000-0000-000000000002"]',
    'UNCLASS'
)
ON CONFLICT (id) DO NOTHING;

-- Disinformation indicators
INSERT INTO infoops_disinformation_indicators (
    id, indicator_type, title, description, platform,
    detected_at, confidence_score,
    linked_campaign_id, linked_narrative_id,
    is_verified, classification
) VALUES
(
    'c1000000-0000-0000-0000-000000000001',
    'BOT_NETWORK',
    'Coordinated bot network amplifying energy FUD hashtags',
    'Network of ~4,200 bot accounts identified posting identical energy-crisis content across multiple platforms within seconds of each other.',
    'SOCIAL_MEDIA',
    '2023-09-12T08:00:00Z', 0.920,
    'b1000000-0000-0000-0000-000000000001',
    'a1000000-0000-0000-0000-000000000001',
    true, 'UNCLASS'
),
(
    'c1000000-0000-0000-0000-000000000002',
    'DEEPFAKE_CONTENT',
    'Deepfake video of Taiwanese official endorsing reunification',
    'AI-generated video depicting a senior Taiwanese government official publicly endorsing peaceful reunification with mainland China.',
    'VIDEO_PLATFORM',
    '2024-01-20T14:30:00Z', 0.870,
    'b1000000-0000-0000-0000-000000000002',
    'a1000000-0000-0000-0000-000000000002',
    true, 'UNCLASS'
),
(
    'c1000000-0000-0000-0000-000000000003',
    'COORDINATED_INAUTHENTIC_BEHAVIOR',
    'Coordinated amplification of NATO instability narrative',
    'Cross-platform CIB detected: 800+ accounts across Twitter, Facebook, and Telegram sharing fabricated NATO internal documents.',
    'SOCIAL_MEDIA',
    '2023-11-05T10:15:00Z', 0.780,
    'b1000000-0000-0000-0000-000000000001',
    'a1000000-0000-0000-0000-000000000003',
    false, 'UNCLASS'
)
ON CONFLICT (id) DO NOTHING;
