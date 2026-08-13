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
