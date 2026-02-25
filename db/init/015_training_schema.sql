-- Training Mode Schema
-- Exercise management, scripted inject system, and trainee performance scoring.

CREATE TABLE IF NOT EXISTS training_exercises (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                TEXT NOT NULL,
    description         TEXT,
    scenario_id         UUID,
    instructor_id       TEXT NOT NULL,
    trainee_ids         JSONB NOT NULL DEFAULT '[]',
    status              TEXT NOT NULL DEFAULT 'DRAFT',
    classification      TEXT NOT NULL DEFAULT 'UNCLASS',
    planned_start       TIMESTAMPTZ,
    actual_start        TIMESTAMPTZ,
    actual_end          TIMESTAMPTZ,
    learning_objectives JSONB NOT NULL DEFAULT '[]',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_training_exercises_status         ON training_exercises (status);
CREATE INDEX IF NOT EXISTS idx_training_exercises_instructor     ON training_exercises (instructor_id);
CREATE INDEX IF NOT EXISTS idx_training_exercises_classification ON training_exercises (classification);
CREATE INDEX IF NOT EXISTS idx_training_exercises_created        ON training_exercises (created_at DESC);

CREATE TABLE IF NOT EXISTS training_injects (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exercise_id                 UUID NOT NULL REFERENCES training_exercises(id) ON DELETE CASCADE,
    inject_type                 TEXT NOT NULL,
    trigger_type                TEXT NOT NULL,
    title                       TEXT NOT NULL,
    description                 TEXT,
    payload                     JSONB NOT NULL DEFAULT '{}',
    trigger_time_offset_minutes INT,
    trigger_event               TEXT,
    trigger_condition           TEXT,
    status                      TEXT NOT NULL DEFAULT 'PENDING',
    injected_at                 TIMESTAMPTZ,
    acknowledged_by             TEXT,
    acknowledged_at             TIMESTAMPTZ,
    classification              TEXT NOT NULL DEFAULT 'UNCLASS',
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_training_injects_exercise    ON training_injects (exercise_id);
CREATE INDEX IF NOT EXISTS idx_training_injects_status      ON training_injects (status);
CREATE INDEX IF NOT EXISTS idx_training_injects_type        ON training_injects (inject_type);
CREATE INDEX IF NOT EXISTS idx_training_injects_created     ON training_injects (created_at ASC);

CREATE TABLE IF NOT EXISTS training_objectives (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exercise_id       UUID NOT NULL REFERENCES training_exercises(id) ON DELETE CASCADE,
    objective_type    TEXT NOT NULL,
    description       TEXT NOT NULL,
    expected_response TEXT,
    weight            NUMERIC(4,3) NOT NULL DEFAULT 1.0,
    status            TEXT NOT NULL DEFAULT 'PENDING',
    actual_response   TEXT,
    score             NUMERIC(5,2),
    scorer_id         TEXT,
    scored_at         TIMESTAMPTZ,
    feedback          TEXT,
    classification    TEXT NOT NULL DEFAULT 'UNCLASS',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_training_objectives_exercise ON training_objectives (exercise_id);
CREATE INDEX IF NOT EXISTS idx_training_objectives_status   ON training_objectives (status);
CREATE INDEX IF NOT EXISTS idx_training_objectives_type     ON training_objectives (objective_type);

-- ---------------------------------------------------------------------------
-- Seed data
-- ---------------------------------------------------------------------------

INSERT INTO training_exercises (
    id, name, description, instructor_id, trainee_ids, status, classification,
    planned_start, learning_objectives
) VALUES (
    'b1a00001-0000-4000-a000-000000000001',
    'Operation Dawn - Entry Exercise',
    'Entry-level combined arms exercise focusing on situational awareness, reporting, and basic tactical decision-making.',
    'instructor-001',
    '["trainee-001", "trainee-002", "trainee-003"]',
    'DRAFT',
    'UNCLASS',
    NOW() + INTERVAL '7 days',
    '["Complete a SITREP within 10 minutes of initial contact", "Issue a fragmentary order (FRAGO) to subordinate units", "Establish communications with higher HQ within 5 minutes"]'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO training_exercises (
    id, name, description, instructor_id, trainee_ids, status, classification,
    actual_start, actual_end, learning_objectives
) VALUES (
    'b1a00002-0000-4000-a000-000000000002',
    'CBRN Incident Response Drill',
    'Completed exercise evaluating trainee proficiency in CBRN agent identification, contamination control, and decontamination procedures.',
    'instructor-001',
    '["trainee-004", "trainee-005"]',
    'COMPLETED',
    'UNCLASS',
    NOW() - INTERVAL '2 days',
    NOW() - INTERVAL '1 day',
    '["Identify CBRN agent type from symptoms and sensor readings", "Initiate proper contamination control procedures", "Submit a CBRN spot report within 15 minutes"]'
) ON CONFLICT (id) DO NOTHING;

-- Injects for Exercise 1 (Operation Dawn)
INSERT INTO training_injects (
    exercise_id, inject_type, trigger_type, title, description, payload,
    trigger_time_offset_minutes, classification
) VALUES (
    'b1a00001-0000-4000-a000-000000000001',
    'ENEMY_ATTACK',
    'TIME_BASED',
    'Hostile contact — Grid 445621',
    'OPFOR elements have been observed moving through Grid 445621. Trainees must report contact and request fire support.',
    '{"grid": "445621", "unit_size": "platoon", "direction": "north"}',
    15,
    'UNCLASS'
) ON CONFLICT DO NOTHING;

INSERT INTO training_injects (
    exercise_id, inject_type, trigger_type, title, description, payload,
    trigger_time_offset_minutes, classification
) VALUES (
    'b1a00001-0000-4000-a000-000000000001',
    'COMMS_DEGRADATION',
    'TIME_BASED',
    'Radio comms degraded — switch to alternate frequency',
    'Primary radio net is experiencing jamming. Trainees must switch to alternate frequency and re-establish communications.',
    '{"primary_freq": "34.500", "alternate_freq": "46.750", "cause": "electronic_jamming"}',
    30,
    'UNCLASS'
) ON CONFLICT DO NOTHING;

INSERT INTO training_injects (
    exercise_id, inject_type, trigger_type, title, description, payload,
    classification
) VALUES (
    'b1a00001-0000-4000-a000-000000000001',
    'COMMAND_MESSAGE',
    'MANUAL',
    'Change of mission — defend in place',
    'Higher HQ has issued a change of mission. Units are to defend in place and await further orders.',
    '{"new_mission": "defend_in_place", "priority": "immediate", "auth": "SUNRAY"}',
    'UNCLASS'
) ON CONFLICT DO NOTHING;

-- Injects for Exercise 2 (CBRN Drill)
INSERT INTO training_injects (
    exercise_id, inject_type, trigger_type, title, description, payload,
    trigger_time_offset_minutes, status, injected_at, acknowledged_by, acknowledged_at, classification
) VALUES (
    'b1a00002-0000-4000-a000-000000000002',
    'CBRN_ALERT',
    'TIME_BASED',
    'Nerve agent detected — VX',
    'Chemical agent detector indicates presence of VX nerve agent. Casualties reported. MOPP 4 required.',
    '{"agent": "VX", "concentration_mg_m3": 0.002, "wind_direction": "SW", "wind_speed_kmh": 12}',
    5,
    'ACKNOWLEDGED',
    NOW() - INTERVAL '1 day 23 hours',
    'trainee-004',
    NOW() - INTERVAL '1 day 22 hours 58 minutes',
    'UNCLASS'
) ON CONFLICT DO NOTHING;

INSERT INTO training_injects (
    exercise_id, inject_type, trigger_type, title, description, payload,
    trigger_time_offset_minutes, status, injected_at, acknowledged_by, acknowledged_at, classification
) VALUES (
    'b1a00002-0000-4000-a000-000000000002',
    'FRIENDLY_CASUALTIES',
    'EVENT_BASED',
    '3 x casualties — decontamination required',
    'Three personnel have been exposed. Decontamination and medical support required.',
    '{"casualties": 3, "contamination_level": "high", "decon_station_required": true}',
    20,
    'ACKNOWLEDGED',
    NOW() - INTERVAL '1 day 22 hours',
    'trainee-005',
    NOW() - INTERVAL '1 day 21 hours 55 minutes',
    'UNCLASS'
) ON CONFLICT DO NOTHING;

-- Objectives for Exercise 1
INSERT INTO training_objectives (
    exercise_id, objective_type, description, expected_response, weight, classification
) VALUES (
    'b1a00001-0000-4000-a000-000000000001',
    'REPORT',
    'Submit a contact report within 10 minutes of OPFOR sighting',
    'SALUTE report submitted to higher HQ within 10 minutes',
    1.0,
    'UNCLASS'
) ON CONFLICT DO NOTHING;

INSERT INTO training_objectives (
    exercise_id, objective_type, description, expected_response, weight, classification
) VALUES (
    'b1a00001-0000-4000-a000-000000000001',
    'DECISION',
    'Issue a FRAGO to adjust defensive positions after OPFOR contact',
    'FRAGO issued within 5 minutes, clearly communicating new positions and tasks',
    1.5,
    'UNCLASS'
) ON CONFLICT DO NOTHING;

INSERT INTO training_objectives (
    exercise_id, objective_type, description, expected_response, weight, classification
) VALUES (
    'b1a00001-0000-4000-a000-000000000001',
    'COMMUNICATION',
    'Re-establish comms with higher HQ within 5 minutes of comms degradation inject',
    'Voice comms confirmed on alternate frequency within 5 minutes',
    0.8,
    'UNCLASS'
) ON CONFLICT DO NOTHING;

-- Objectives for Exercise 2 (scored)
INSERT INTO training_objectives (
    exercise_id, objective_type, description, expected_response, weight,
    status, actual_response, score, scorer_id, scored_at, feedback, classification
) VALUES (
    'b1a00002-0000-4000-a000-000000000002',
    'ACTION',
    'Correctly identify CBRN agent type and initiate MOPP 4',
    'VX identified, MOPP 4 initiated within 3 minutes',
    1.0,
    'MET',
    'Identified VX via M8A1 alarm, MOPP 4 within 2 minutes 45 seconds',
    88.0,
    'instructor-001',
    NOW() - INTERVAL '20 hours',
    'Good identification but slight delay in donning gloves',
    'UNCLASS'
) ON CONFLICT DO NOTHING;

INSERT INTO training_objectives (
    exercise_id, objective_type, description, expected_response, weight,
    status, actual_response, score, scorer_id, scored_at, feedback, classification
) VALUES (
    'b1a00002-0000-4000-a000-000000000002',
    'REPORT',
    'Submit CBRN spot report within 15 minutes',
    'Complete CBRN spot report transmitted to higher HQ within 15 minutes',
    1.0,
    'PARTIALLY_MET',
    'Spot report submitted at 18 minutes; missing agent concentration field',
    62.0,
    'instructor-001',
    NOW() - INTERVAL '20 hours',
    'Report submitted but late and incomplete — review CBRN report format',
    'UNCLASS'
) ON CONFLICT DO NOTHING;

INSERT INTO training_objectives (
    exercise_id, objective_type, description, expected_response, weight,
    status, actual_response, score, scorer_id, scored_at, feedback, classification
) VALUES (
    'b1a00002-0000-4000-a000-000000000002',
    'ASSESSMENT',
    'Assess decontamination requirements and establish decon station',
    'Decon station established, casualties processed within 20 minutes',
    1.2,
    'MET',
    'Decon station established at 14 minutes, all 3 casualties processed per SOP',
    95.0,
    'instructor-001',
    NOW() - INTERVAL '20 hours',
    'Excellent execution — well-practiced drills evident',
    'UNCLASS'
) ON CONFLICT DO NOTHING;
