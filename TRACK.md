# TRACK.md — Append-Only Development Log

> **Rule:** NEVER delete or edit past entries. Always append at the top (most-recent-first) OR at the bottom (chronological). This project uses **chronological order** (append at the bottom).
> Each entry starts with `## YYYY-MM-DD — <Story ID or Sprint>`.

---

## 2026-08-13 — Sprint 0 (Kickoff)

**What was done:**
- Reviewed `prompt.md` in full; internalized epics, story points, Gherkin ACs, DoD, and tech stack.
- Generated full sprint plan (8 sprints, ~81 pts) sequenced by dependency.
- Created tracking system files: `BACKLOG.md`, `SPRINT.md`, `TASK.md`, `TRACK.md`, `RETRO.md`.
- `BACKLOG.md` pre-filled with all epics, stories, points, and dependency notes from §5.
- `SPRINT.md` pre-filled for Sprint 0 with task checklist and sign-off criteria.
- `TASK.md` scaffold written (will be rewritten per-story starting Sprint 1).
- `docs/adr/` directory created; ADR seed files pending.

**Decisions made:**
- Sprint sequencing confirmed: Ingestion → Cleaning → DB Opt → A/B → ML → Dashboard+n8n → Frontend.
- Sprint 0 scoped to infrastructure only — no feature code, no tests yet.
- Tracking files use chronological append order (oldest entry first, newest last).

**Blockers:** None.

**Next:**
- Await user confirmation to begin Sprint 0 execution (folder structure, schema, ADRs, README, git init).
- On approval: execute all Sprint 0 tasks, commit, tag `v0.0.0-sprint0`, update SPRINT.md checkboxes, append TRACK.md entry, write RETRO.md Sprint 0 entry.

---

## 2026-08-13 — Sprint 0 (Execution Complete)

**What was done:**
- Created full folder structure: `ingestion/connectors/`, `cleaning/`, `ab_testing/`, `ml/`, `dashboard/`, `automation/n8n_workflows/`, `db/migrations/`, `docs/adr/`, `tests/`, `models/`
- Wrote `.env.example` with all env vars: PostgreSQL, MySQL, n8n, MODEL_DIR, ENCRYPTION_KEY, LOG_LEVEL
- Wrote `requirements.txt` with pinned versions for all 18 production + dev dependencies
- Configured `pytest.ini`: testpaths=tests, --strict-markers, integration/slow markers
- Wrote `db/migrations/001_initial_schema.sql`: 5 tables in a single transaction with CHECK constraints, DEFAULT values, and UNIQUE constraint for upsert
- Wrote seed ADRs: ADR-001 (upsert), ADR-002 (A/B config object), ADR-003 (query benchmarks)
- Created `__init__.py` for all Python packages; `tests/conftest.py` scaffold
- Wrote `README.md`: setup steps, project structure, known limitations, future work section
- Wrote `.gitignore`: venv, .env, __pycache__, models/*.pkl, coverage, OS/IDE files
- Git: initialized repo, staged all 34 files, committed as root commit `b41a41c`, tagged `v0.0.0-sprint0`
- Updated SPRINT.md (all 9 tasks checked off), BACKLOG.md unchanged (no stories completed — Sprint 0 is infra only)

**Decisions made:**
- Added `dataset_id` column to `raw_ingest` table (not in original prompt schema) — needed so ingestion queries can group rows by upload. Will track in a future ADR if challenged.
- Added `CHECK` constraints to `source_type`, `metric_type`, `task_type`, and `status` columns for data integrity at DB level.
- Used `IF NOT EXISTS` on all `CREATE TABLE` statements so migration is re-runnable safely.
- `models/` directory gitignored for `*.pkl`/`*.joblib` but the directory itself tracked via `.gitkeep`.

**Blockers:** None.

**Next:**
- Begin Sprint 1: US-1.1 (CSV/Excel file ingestion, 5 pts) → US-1.3 (upsert de-duplication, 5 pts)
- Rewrite TASK.md with US-1.1 task breakdown before writing any code.
- Update BACKLOG.md: set US-1.1 to `In Progress`.

---

## 2026-08-13 — US-1.1 + US-1.3 (Sprint 1 Complete)

**What was done:**
- Wrote `ingestion/logger.py`: shared structured JSON logger using `python-json-logger`; level controlled by LOG_LEVEL env var.
- Wrote `db/connection.py`: `get_engine()` reads DATABASE_URL from env; `get_connection()` yields a transactional SQLAlchemy Connection (auto-commit/rollback).
- TDD: wrote `tests/test_file_ingestor.py` (13 tests) BEFORE implementing file_ingestor.py.
- Implemented `ingestion/file_ingestor.py`:
  - `IngestionError` — single domain exception for all bad-file conditions.
  - `parse_csv()`: checks file exists, non-zero size, >0 data rows; raises IngestionError with specific message for each failure mode.
  - `parse_excel()`: same guarantees for .xlsx/.xls.
  - `ingest_file()`: selects parser by extension, generates UUID4 dataset_id, bulk-inserts into `raw_ingest` via parameterised SQL. DB is NOT touched if parsing fails.
  - `upsert_to_clean_records()`: `INSERT ... ON CONFLICT DO UPDATE` on `(dataset_id, unique_key)`; defaults key column to first column.
- TDD: wrote `tests/test_upsert.py` (8 tests) for US-1.3 upsert logic.
- Ran `pytest`: 21/21 PASSED.
- Ran coverage: ingestion/ **95%** (>70% threshold).
- Fixed: `pytest.ini` had UTF-8 BOM (`\ufeff`) from PowerShell `Set-Content -Encoding UTF8` — switched to ASCII encoding.
- Committed as `6ad224b`, tagged `v0.1.0-sprint1`.
- Updated BACKLOG.md: US-1.1, US-1.3 → Done.

**Decisions made:**
- `ingest_file()` uses a single `conn.execute(sql, rows)` call with a list of dicts — SQLAlchemy executemany under the hood. More efficient than per-row execute.
- `parse_csv()` raises `IngestionError` (not `pandas.errors.ParserError`) — consumers shouldn't depend on pandas internals.
- `header_only` files (0 data rows after header) treated the same as empty files — raises `IngestionError("no data rows")`.
- `pytest.ini` must use ASCII encoding on Windows with PowerShell to avoid BOM corruption.

**Blockers:** None.

**Next:**
- Sprint 2: US-1.2 (API/PostgreSQL/MySQL connectors, 8 pts) → US-2.1 (auto data cleaning, 3 pts).
- Rewrite TASK.md with US-1.2 breakdown; set US-1.2 to In Progress in BACKLOG.md.

---

## 2026-08-13 — US-1.2 + US-2.1 (Sprint 2 Complete)

**What was done:**
- Wrote `ingestion/connectors/base.py`: defined `BaseConnector` ABC with `test_connection()` and `fetch()`, plus `ConnectorError`.
- Wrote `ingestion/connectors/api_connector.py`: REST API data loader using `requests` with status testing, custom headers, and JSON list parsing.
- Wrote `ingestion/connectors/postgres_connector.py`: PostgreSQL connector using SQLAlchemy Core engine (no ORM overhead).
- Wrote `ingestion/connectors/mysql_connector.py`: MySQL connector using SQLAlchemy Core + `pymysql`.
- Wrote `cleaning/cleaner.py`: pure transformation module implementing:
  1. Exact duplicate row removal
  2. HTML tag (`<[^>]+>`) & Unicode emoji stripping on object/string columns
  3. Dropping high-sparsity columns (>50% missing values)
  4. Imputing remaining missing values (numeric -> median, categorical -> mode)
  5. Returning `(cleaned_df, CleaningReport)` with structured audit trail metrics.
- TDD: written `tests/test_connectors.py` (13 tests) and `tests/test_cleaner.py` (11 tests).
- Updated `.env` with live PostgreSQL database URL (`neondb` on AWS Neon).
- Ran `pytest`: 45/45 PASSED across all test files.
- Ran coverage: `ingestion/` & `cleaning/` **95%** overall.
- Tagged `v0.2.0-sprint2`.
- Updated BACKLOG.md: US-1.2, US-2.1 -> Done.

**Decisions made:**
- Connectors derive from `BaseConnector` ABC and return DataFrames directly so they plug seamlessly into `cleaning/cleaner.py` and `upsert_to_clean_records()`.
- Data cleaner is pure and stateless (no DB dependencies); audit trail captured via `CleaningReport` dataclass.
- Deduplication occurs before missing value imputation to ensure accurate frequency counts for mode calculation.

**Blockers:** None.

**Next:**
- Sprint 3: US-3.1 (DB indexing & query benchmarks, 5 pts).

---

## 2026-08-13 — US-3.1 (Sprint 3 Complete)

**What was done:**
- Wrote `db/benchmark.py`:
  - `parse_explain_output()`: parses PostgreSQL `EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)` output for execution time (ms) and total planner cost.
  - `benchmark_query()`: measures query execution before index creation, creates index, measures query execution after index, calculates speedup ratio.
  - `save_benchmark()`: persists benchmark records into `query_benchmarks` table (ADR-003).
- Wrote `tests/test_benchmark.py` (5 tests): verified EXPLAIN parser regex, speedup calculations, and DB insertion.
- Wrote `scripts/seed_and_benchmark.py`: seeded 10,000 synthetic `clean_records` into live Neon PostgreSQL DB and executed benchmark.
- Results on 10,000 live records:
  - Before index: 21.09 ms (Plan cost: 297.0)
  - After index: 0.08 ms (Plan cost: 8.3)
  - **Speedup: 263.62x faster**
- Ran `pytest`: 50/50 PASSED. Overall coverage: **91%**.
- Tagged `v0.3.0-sprint3`.
- Updated BACKLOG.md: US-3.1 -> Done.

**Decisions made:**
- Benchmark metrics are recorded in PostgreSQL table `query_benchmarks` per ADR-003 so dashboard can display query performance improvements.

**Blockers:** None.

**Next:**
- Sprint 4: US-4.1 (No-code experiment config, 8 pts) & US-4.2 (Statistically valid A/B results, 5 pts).

---

## 2026-08-13 — US-4.1 + US-4.2 (Sprint 4 Complete)

**What was done:**
- Wrote `ab_testing/config.py`: `ExperimentConfig` dataclass and `validate_config()` schema validator enforcing variant_column existence (≥2 distinct groups), metric_column existence, and metric_type ("numeric" | "categorical").
- Wrote `ab_testing/engine.py`:
  - `evaluate_experiment()`: automatically runs Welch's t-test + Cohen's d + 95% CI for numeric metrics, or Chi-square test + Cramér's V for categorical metrics.
  - Computes `is_significant` flag (p < 0.05).
  - `save_experiment_result()`: inserts experiment outcome into PostgreSQL `experiments` table.
- Wrote `tests/test_ab_config.py` (5 tests) and `tests/test_ab_engine.py` (3 tests).
- Ran `pytest`: 58/58 PASSED. Overall coverage: **92%** (ab_testing coverage: **96%**).
- Tagged `v0.4.0-sprint4`.
- Updated BACKLOG.md: US-4.1, US-4.2 -> Done.

**Decisions made:**
- Engine complies strictly with ADR-002: reusable config object passed to general statistical engine (not hardcoded per dataset).

**Blockers:** None.

**Next:**
- Sprint 5: US-5.1 (Train ML model on user-selected target, 8 pts) & US-5.2 (Auto-retrain model when new data arrives, 5 pts).

---

## 2026-08-13 — US-5.1 + US-5.2 (Sprint 5 Complete)

**What was done:**
- Wrote `ml/trainer.py`:
  - `train_model()`: supports Regression (RandomForestRegressor, RMSE, R2) and Classification (RandomForestClassifier, Accuracy, F1 macro).
  - Serializes `.joblib` model artifacts into `models/` directory.
  - `save_prediction_metadata()`: records model metadata in PostgreSQL `predictions` table.
- Wrote `ml/predictor.py`: `predict()` aligns features and computes inference on new input DataFrames.
- Wrote `ml/retrainer.py`: `auto_retrain_if_needed()` checks current vs previously trained row count and triggers auto-retraining when new rows are detected.
- Wrote `tests/test_ml_trainer.py` (4 tests) and `tests/test_ml_retrainer.py` (2 tests).
- Ran `pytest`: 64/64 PASSED. Overall coverage: **93%** (`ml/` coverage: **97%**).
- Tagged `v0.5.0-sprint5`.
- Updated BACKLOG.md: US-5.1, US-5.2 -> Done.

**Decisions made:**
- Models use scikit-learn `RandomForest` defaults with one-hot encoding for categorical features, making the training pipeline fully domain-agnostic.

**Blockers:** None.

**Next:**
- Sprint 6: US-6.1 (Descriptive stats view), US-6.2 (Experiment & prediction results view), US-7.1 (n8n automation workflow).

---

## 2026-08-13 — US-6.1 + US-6.2 + US-7.1 (Sprint 6 Complete)

**What was done:**
- Wrote `dashboard/stats.py`: `compute_summary_stats()` generating mean, std, min, median, max, and missing counts for DataFrame columns.
- Wrote `dashboard/results.py`: SQL loaders and Plotly interactive chart builders for A/B experiment p-values and database query benchmark performance.
- Wrote `dashboard/app.py`: Streamlit dashboard application with sidebar radio navigation across 4 views:
  1. 📊 Descriptive Statistics
  2. 🧪 A/B Testing Results
  3. 🤖 ML Model Predictions
  4. ⚡ DB Query Benchmarks
- Wrote `scripts/run_pipeline.py`: `run_end_to_end_pipeline()` orchestrating ingest -> clean -> upsert -> A/B test -> ML model train sequentially. Supports CLI execution for n8n cron triggers.
- Wrote `tests/test_dashboard_stats.py` (2 tests), `tests/test_dashboard_results.py` (4 tests), `tests/test_pipeline_runner.py` (1 test).
- Ran `pytest`: 71/71 PASSED. Overall coverage: **93%**.
- Tagged `v0.6.0-sprint6`.
- Updated BACKLOG.md: US-6.1, US-6.2, US-7.1 -> Done.

**Decisions made:**
- Streamlit application uses parameterised SQL queries against `get_connection()` context manager to keep DB access clean and injection-safe.

**Blockers:** None.

**Next:**
- Sprint 7: US-8.1 (Form-driven experiment creation, 8 pts) & US-8.2 (Plain-language results summary, 3 pts).

---

## 2026-08-13 — US-8.1 + US-8.2 (Sprint 7 & Final Project Release)

**What was done:**
- Wrote `dashboard/narrative.py`:
  - `generate_ab_narrative()`: translates p-values, effect sizes, test types, and mean differences into clear English text highlighting statistical significance.
  - `generate_ml_narrative()`: translates R2/RMSE or Accuracy/F1 scores into plain-language model quality summaries.
- Updated `dashboard/app.py`:
  - Added interactive "Create A/B Experiment" Streamlit form allowing non-technical users to select datasets, variant/metric columns, and execute experiments on the fly.
  - Integrated plain-language summary cards into A/B Results and ML Predictions tabs.
- Wrote `tests/test_narrative.py` (4 tests) and `tests/test_dashboard_forms.py` (1 test).
- Ran `pytest`: 76/76 PASSED across all modules. Overall coverage: **80%**.
- Tagged `v1.0.0-final`.
- Updated BACKLOG.md: All stories (US-1.1 through US-8.2) marked **Done**.

**Decisions made:**
- Self-service UI allows zero-code execution of statistical experiments and instant rendering of plain-language business insights.

**Blockers:** None.

**Status:** Project complete. 81 points delivered across 7 sprints.
