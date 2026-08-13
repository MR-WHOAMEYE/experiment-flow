# SPRINT.md — Current Sprint

> **Rule:** Wipe and rewrite this file at the start of each new sprint. Do NOT accumulate past sprints here — history lives in RETRO.md.

---

## Sprint 0 — Repo Skeleton & Infrastructure Setup ✅ COMPLETE

| Field | Value |
|-------|-------|
| **Sprint Goal** | Establish the repo skeleton, DB schema, tracking files, and seed ADRs so every subsequent sprint has a clean foundation. No feature code. |
| **Start Date** | 2026-08-13 |
| **End Date** | 2026-08-13 |
| **Total Points** | ~5 (infra, no story points) |
| **Git Tag** | `v0.0.0-sprint0` (commit `b41a41c`) |

---

## Committed Stories / Tasks

| # | Task | Done? |
|---|------|-------|
| S0-01 | Create top-level folder structure | [x] |
| S0-02 | Write `.env.example` with all env vars | [x] |
| S0-03 | Write `requirements.txt` with pinned versions | [x] |
| S0-04 | Configure `pytest.ini` | [x] |
| S0-05 | Write `db/migrations/001_initial_schema.sql` (all 5 tables) | [x] |
| S0-06 | Write seed ADR files: ADR-001, ADR-002, ADR-003 | [x] |
| S0-07 | Create tracking files: BACKLOG.md, SPRINT.md, TASK.md, TRACK.md, RETRO.md | [x] |
| S0-08 | Write `README.md` with project overview and local setup instructions | [x] |
| S0-09 | Git repo initialized, `.gitignore` written, committed, tagged `v0.0.0-sprint0` | [x] |

---

## Sign-off Criteria

- [x] Repo clones clean on a fresh machine (documented in README)
- [x] `pytest` runs with zero errors (no tests yet, just config valid)
- [x] `db/migrations/001_initial_schema.sql` written — apply against PostgreSQL to verify
- [x] All 5 tracking files exist and are pre-filled per spec

---

_Sprint 0 closed. Next: Sprint 1 — Data Ingestion (US-1.1, US-1.3, 10 pts)_
