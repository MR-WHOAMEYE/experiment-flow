# TASK.md — Active Story: US-3.1

**Story:** US-3.1 — Database & Query Optimization
**Sprint:** 3 | **Status:** ✅ Complete

---

## Task Breakdown

### US-3.1 — DB & Query Optimization (5 pts)
- [x] `db/benchmark.py`:
  - [x] `parse_explain_output()` — extracts execution time (ms) and total planner cost from raw PostgreSQL EXPLAIN output
  - [x] `benchmark_query()` — executes query before/after index creation and measures timings
  - [x] `save_benchmark()` — records result in `query_benchmarks` table
- [x] `tests/test_benchmark.py` (5 tests):
  - [x] EXPLAIN output parser regex validation
  - [x] Speedup multiplier computation
  - [x] `query_benchmarks` DB insertion mock
- [x] `scripts/seed_and_benchmark.py`:
  - [x] Seeded 10,000 synthetic records into `clean_records`
  - [x] Measured baseline query execution time (21.09 ms, cost 297.0) vs indexed execution time (0.08 ms, cost 8.3)
  - [x] Verified **263.62x speedup** on live Neon PostgreSQL database
