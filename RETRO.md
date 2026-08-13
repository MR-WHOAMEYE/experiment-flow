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
