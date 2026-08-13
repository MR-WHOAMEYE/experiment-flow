# ADR-003 — Store Query Benchmarks in a DB Table, Not Just Logs

**Date:** 2026-08-13
**Status:** Accepted — Non-negotiable (per prompt.md §3)
**Story:** US-3.1

---

## Context

To demonstrate database query optimization (EXPLAIN ANALYZE before/after indexing), the benchmark results must persist beyond a single terminal session and be queryable/reportable in the dashboard.

## Decision

EXPLAIN ANALYZE output (execution time in ms, planner cost) is parsed and stored in the `query_benchmarks` table:

```sql
CREATE TABLE query_benchmarks (
    id               BIGSERIAL PRIMARY KEY,
    query_label      TEXT NOT NULL,
    before_ms        NUMERIC,
    after_ms         NUMERIC,
    before_plan_cost NUMERIC,
    after_plan_cost  NUMERIC,
    recorded_at      TIMESTAMPTZ DEFAULT now()
);
```

A `db/benchmark.py` module runs EXPLAIN ANALYZE for each query pattern before and after indexing, parses the output, and inserts into this table.

## Alternatives Considered

| Alternative | Reason Rejected |
|-------------|-----------------|
| Log to console only | Results lost after session; can't query them in the dashboard |
| Log to a flat file (CSV/JSON) | Not queryable; diverges from the project's PostgreSQL-first approach |
| Store raw EXPLAIN ANALYZE text as TEXT/JSONB | Harder to aggregate and chart; parsing is done once at insert time |

## Consequences

- **Positive:** Benchmark results survive session restarts and are reportable in the dashboard.
- **Positive:** Can query improvement ratios with SQL (`(before_ms - after_ms) / before_ms * 100`).
- **Positive:** Makes the optimization story verifiable and reproducible.
- **Negative:** Requires parsing EXPLAIN ANALYZE text output, which is version-sensitive — pin PostgreSQL version and document.
- **Negative:** Adds a small amount of schema overhead; acceptable at capstone scale.
