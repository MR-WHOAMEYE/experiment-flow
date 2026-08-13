# ADR-001 — Use PostgreSQL Upsert for Re-uploaded File Sources

**Date:** 2026-08-13
**Status:** Accepted
**Story:** US-1.3

---

## Context

When a user re-uploads a file that has already been ingested, naive `INSERT` statements would create duplicate rows in `clean_records`. This degrades query results and breaks analytic correctness.

## Decision

Use PostgreSQL `INSERT ... ON CONFLICT DO UPDATE` (upsert) keyed on `(dataset_id, unique_key)` in `clean_records`.

- `unique_key` is derived from a user-designated column or defaults to the first column of the uploaded file.
- The `UNIQUE (dataset_id, unique_key)` constraint in the schema enforces integrity at the DB level, not just in application code.

## Alternatives Considered

| Alternative | Reason Rejected |
|-------------|-----------------|
| `DELETE` existing rows then bulk `INSERT` | Loses audit trail; not atomic without a transaction wrapper; slower for partial re-uploads |
| Application-level de-duplication (check before insert) | Race condition under concurrent uploads; two round-trips instead of one |
| Separate "staging" table with merge job | Over-engineering for capstone scope |

## Consequences

- **Positive:** Single SQL statement, atomic, leverages PostgreSQL's native conflict resolution.
- **Positive:** Re-upload is idempotent — safe to run multiple times.
- **Negative:** Requires the user to identify (or accept the default) unique key column at upload time.
- **Negative:** If the schema of the uploaded file changes between uploads (column added/removed), the upsert may behave unexpectedly — document this limitation in the README.
