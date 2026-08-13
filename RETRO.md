# RETRO.md — Sprint Retrospectives

> **Rule:** NEVER delete or edit past entries. Append one entry per completed sprint at the bottom.

---

## Sprint 0 Retrospective — 2026-08-13

**Sprint Goal:** Repo skeleton, DB schema, ADR seeds, tracking files — no feature code.
**Stories Completed:** N/A (infrastructure sprint)
**Stories Carried Over:** None

### What Went Well
- All 9 Sprint 0 tasks completed in a single session.
- DB schema written with proper constraints (`CHECK`, `UNIQUE`, `IF NOT EXISTS`) — more robust than the first-draft prompt schema.
- Tracking system (BACKLOG/SPRINT/TASK/TRACK/RETRO) fully operational before any code was written.
- ADR seeds written with proper context, decision rationale, and alternatives-considered — not just decision statements.

### What Didn't Go Well
- `dataset_id` column was missing from the original `raw_ingest` schema in `prompt.md` — had to add it during migration writing. This is a minor schema deviation that should be captured in an ADR (deferred — low risk at Sprint 0 stage).
- LF/CRLF warnings on Windows during `git add` — cosmetic, suppressed by `.gitattributes` (add in Sprint 1 if it causes issues).

### One Concrete Change for Next Sprint
- **Sprint 1**: Before writing `ingestion/file_ingestor.py`, write the test file skeleton first (TDD approach) so implementation directly targets the acceptance criteria from the Gherkin scenarios. This avoids retrofitting tests after the fact.

---

<!-- Template for future sprints:

## Sprint N Retrospective — YYYY-MM-DD

**Sprint Goal:** <goal>
**Stories Completed:** <list>
**Stories Carried Over:** <list or "None">

### What Went Well
-

### What Didn't Go Well
-

### One Concrete Change for Next Sprint
-

-->

---

## Sprint 1 Retrospective — 2026-08-13

**Sprint Goal:** Users can upload CSV/Excel files; data loads into `raw_ingest`; re-uploads upsert without duplicates.
**Stories Completed:** US-1.1 (5 pts), US-1.3 (5 pts) — 10/10 pts
**Stories Carried Over:** None

### What Went Well
- TDD approach worked well: writing tests before implementation caught the need for specific IngestionError messages (e.g., "not found" vs "empty" vs "no data rows") that made all AC assertions pass cleanly.
- 21/21 tests passed first run after implementation.
- 95% coverage on `ingestion/` — significantly above the 70% floor.
- `upsert_to_clean_records()` cleanly implements ADR-001 with a single SQL statement; no application-level pre-check needed.
- `db/connection.py` is a clean shared abstraction — no module will construct its own engine.

### What Didn't Go Well
- `pytest.ini` BOM bug: PowerShell `Set-Content -Encoding UTF8` on Windows prepends a UTF-8 BOM (`\ufeff`) which pytest cannot parse. Fixed by switching to `-Encoding ASCII`. This is a Windows-specific gotcha that cost one failed run.
- The `malformed_csv` fixture (inconsistent column counts) did not actually cause a parse error with pandas default settings — pandas was lenient. Need to revisit if stricter CSV validation is required (noted for future).

### One Concrete Change for Next Sprint
- **Sprint 2**: All `.env.example` env vars needed for new connectors must be identified and added BEFORE writing any connector code — not discovered mid-implementation. This avoids the credential-handling being an afterthought.

---

## Sprint 2 Retrospective — 2026-08-13

**Sprint Goal:** Users can connect API/PostgreSQL/MySQL sources; all ingested data is automatically cleaned before analysis.
**Stories Completed:** US-1.2 (8 pts), US-2.1 (3 pts) — 11/11 pts
**Stories Carried Over:** None

### What Went Well
- Pure component architecture: `cleaner.py` operates directly on DataFrames, making it 100% testable without DB mocks.
- `BaseConnector` standard interface made adding API, PostgreSQL, and MySQL connectors straightforward.
- Overall code coverage reached 95% across `ingestion` and `cleaning`.
- All 45 unit tests passed.

### What Didn't Go Well
- In `test_cleaner.py`, testing single-column DataFrame deduplication required explicit `id` column assignment so deduplication didn't shrink row indices unexpectedly before mode assertion.

### One Concrete Change for Next Sprint
- **Sprint 3**: When benchmarking DB queries (EXPLAIN ANALYZE per ADR-003), ensure both indexed and unindexed table states are clean and isolated so benchmark timing measurements in `query_benchmarks` are accurate.

---

## Sprint 3 Retrospective — 2026-08-13

**Sprint Goal:** Common query patterns on `clean_records` are indexed; before/after performance is benchmarked using `EXPLAIN ANALYZE` and recorded in `query_benchmarks`.
**Stories Completed:** US-3.1 (5 pts) — 5/5 pts
**Stories Carried Over:** None

### What Went Well
- Real empirical verification: tested on 10,000 synthetic records against live Neon PostgreSQL database.
- Measurable impact: `EXPLAIN ANALYZE` demonstrated a **263.62x speedup** (21.09 ms -> 0.08 ms) after creating composite index `(dataset_id, unique_key)`.
- 50/50 unit tests passing with 91% code coverage.

### What Didn't Go Well
- None. Benchmark parser and live DB execution worked cleanly.

### One Concrete Change for Next Sprint
- **Sprint 4**: Ensure `ExperimentConfig` validation (ADR-002) raises clear domain exceptions (`ConfigValidationError`) when requested variant/metric columns do not exist in `clean_records`.

---

## Sprint 4 Retrospective — 2026-08-13

**Sprint Goal:** Users can configure and execute statistically valid A/B experiments (t-test / chi-square) with p-value, effect size, and confidence intervals stored in DB.
**Stories Completed:** US-4.1 (8 pts), US-4.2 (5 pts) — 13/13 pts
**Stories Carried Over:** None

### What Went Well
- Pure statistical engine decouples test logic from DB loading, allowing 100% synthetic DataFrame testing.
- ADR-002 design validated: single ExperimentConfig object works seamlessly for both numeric and categorical metrics.
- 58/58 unit tests passing with 92% code coverage.

### What Didn't Go Well
- Reserved logging key collision: `extra={"name": ...}` in Python logging collided with `LogRecord.name`. Renamed extra parameter to `exp_name`.

### One Concrete Change for Next Sprint
- **Sprint 5**: Ensure serialized ML models (`models/*.pkl`) are stored in `models/` directory while their metadata and metrics (RMSE, R2, Accuracy) are recorded in the `predictions` DB table.
