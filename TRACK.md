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
