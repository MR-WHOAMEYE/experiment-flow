-- ============================================================
-- Migration: 001_initial_schema
-- Description: Create all core tables for the EaaS platform.
-- Applies to: PostgreSQL 15+
-- Run with: psql -U <user> -d <db> -f 001_initial_schema.sql
-- ============================================================

BEGIN;

-- -------------------------------------------------------
-- raw_ingest: stores every row exactly as received,
-- one record per source row, payload as JSONB.
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw_ingest (
    id           BIGSERIAL    PRIMARY KEY,
    source_type  TEXT         NOT NULL CHECK (source_type IN (''csv'', ''excel'', ''api'', ''postgres'', ''mysql'', ''scrape'')),
    source_name  TEXT         NOT NULL,
    dataset_id   TEXT         NOT NULL,   -- groups rows from the same upload/pull
    ingested_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    payload      JSONB        NOT NULL
);

-- -------------------------------------------------------
-- clean_records: cleaned, structured data ready for analysis.
-- unique_key enables upsert de-duplication (ADR-001).
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS clean_records (
    id           BIGSERIAL    PRIMARY KEY,
    dataset_id   TEXT         NOT NULL,
    unique_key   TEXT,
    cleaned_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    fields       JSONB        NOT NULL,
    UNIQUE (dataset_id, unique_key)
);

-- -------------------------------------------------------
-- experiments: A/B experiment config + results (ADR-002).
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS experiments (
    id              BIGSERIAL    PRIMARY KEY,
    name            TEXT         NOT NULL,
    dataset_id      TEXT         NOT NULL,
    variant_column  TEXT         NOT NULL,
    metric_column   TEXT         NOT NULL,
    metric_type     TEXT         NOT NULL CHECK (metric_type IN (''numeric'', ''categorical'')),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    p_value         NUMERIC,
    lift_pct        NUMERIC,
    significant     BOOLEAN,
    status          TEXT         NOT NULL DEFAULT ''pending''
                                 CHECK (status IN (''pending'', ''running'', ''complete'', ''failed''))
);

-- -------------------------------------------------------
-- predictions: ML model training runs + metric results.
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS predictions (
    id             BIGSERIAL    PRIMARY KEY,
    dataset_id     TEXT         NOT NULL,
    target_column  TEXT         NOT NULL,
    task_type      TEXT         NOT NULL CHECK (task_type IN (''regression'', ''classification'')),
    trained_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    metric_name    TEXT,                              -- rmse | mae | f1 | accuracy
    metric_value   NUMERIC,
    model_path     TEXT                               -- path to serialized .pkl file
);

-- -------------------------------------------------------
-- query_benchmarks: EXPLAIN ANALYZE before/after results (ADR-003).
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS query_benchmarks (
    id               BIGSERIAL    PRIMARY KEY,
    query_label      TEXT         NOT NULL,
    before_ms        NUMERIC,
    after_ms         NUMERIC,
    before_plan_cost NUMERIC,
    after_plan_cost  NUMERIC,
    recorded_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

COMMIT;

-- ============================================================
-- Verification queries (run manually after migration):
-- SELECT table_name FROM information_schema.tables
--   WHERE table_schema = ''public''
--   ORDER BY table_name;
-- Expected: clean_records, experiments, predictions,
--           query_benchmarks, raw_ingest
-- ============================================================
