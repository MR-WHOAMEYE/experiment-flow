# SPRINT.md — Current Sprint

> **Rule:** Wipe and rewrite this file at the start of each new sprint. History lives in RETRO.md.

---

## Sprint 3 — Database & Query Optimization ✅ COMPLETE

| Field | Value |
|-------|-------|
| **Sprint Goal** | Common query patterns on `clean_records` are indexed; before/after performance is benchmarked using `EXPLAIN ANALYZE` and recorded in `query_benchmarks`. |
| **Start Date** | 2026-08-13 |
| **End Date** | 2026-08-13 |
| **Total Points** | 5 |
| **Git Tag** | `v0.3.0-sprint3` |

---

## Stories

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| US-3.1 | Index common queries; benchmark before/after | 5 | ✅ Done |

---

## Story Checklist

### US-3.1 — DB & Query Optimization
- [x] `db/benchmark.py` — `parse_explain_output()`, `benchmark_query()`, `save_benchmark()`
- [x] `tests/test_benchmark.py` — 5 unit tests for EXPLAIN parser, benchmark execution, and DB storage
- [x] `scripts/seed_and_benchmark.py` — seeded 10,000 synthetic records on live PostgreSQL database
- [x] Verified `EXPLAIN ANALYZE` speedup (21.09 ms -> 0.08 ms, **263.62x faster**)
- [x] Recorded benchmark in `query_benchmarks` table
- [x] 50/50 tests PASSED | overall coverage: 91%

---

## Sign-off
- [x] 50/50 tests pass — `pytest`
- [x] Coverage: `db/`, `ingestion/`, `cleaning/` **91%** (threshold: 70%)
- [x] Gherkin ACs verified with 10,000+ records on live Neon PostgreSQL DB
- [x] BACKLOG.md: US-3.1 → Done
- [x] TRACK.md entry appended
- [x] RETRO.md Sprint 3 entry written
- [x] Tag: `v0.3.0-sprint3`

_Sprint 3 closed. Next: Sprint 4 — A/B Testing Engine (US-4.1, US-4.2, 13 pts)_
