# SPRINT.md — Current Sprint

> **Rule:** Wipe and rewrite this file at the start of each new sprint. Do NOT accumulate past sprints here — history lives in RETRO.md.

---

## Sprint 0 — Repo Skeleton & Infrastructure Setup

| Field | Value |
|-------|-------|
| **Sprint Goal** | Establish the repo skeleton, DB schema, tracking files, and seed ADRs so every subsequent sprint has a clean foundation. No feature code. |
| **Start Date** | 2026-08-13 |
| **Target End Date** | 2026-08-13 |
| **Total Points** | ~5 (infra, no story points) |

---

## Committed Stories / Tasks

| # | Task | Done? |
|---|------|-------|
| S0-01 | Create top-level folder structure (`ingestion/`, `cleaning/`, `ab_testing/`, `ml/`, `dashboard/`, `automation/`, `db/migrations/`, `docs/adr/`, `tests/`) | [ ] |
| S0-02 | Write `.env.example` with all env vars | [ ] |
| S0-03 | Write `requirements.txt` with pinned versions | [ ] |
| S0-04 | Configure `pytest.ini` (testpaths, coverage ≥70%) | [ ] |
| S0-05 | Write `db/migrations/001_initial_schema.sql` (all 5 tables) | [ ] |
| S0-06 | Write seed ADR files: ADR-001, ADR-002, ADR-003 | [ ] |
| S0-07 | Create tracking files: BACKLOG.md, SPRINT.md, TASK.md, TRACK.md, RETRO.md | [ ] |
| S0-08 | Write `README.md` with project overview and local setup instructions | [ ] |
| S0-09 | Initialize git repo, add `.gitignore`, commit Sprint 0, tag `v0.0.0-sprint0` | [ ] |

---

## Sign-off Criteria
- [ ] Repo clones clean on a fresh machine (documented in README)
- [ ] `pytest` runs with zero errors (no tests yet, just config valid)
- [ ] `db/migrations/001_initial_schema.sql` applies without error against a local PostgreSQL instance
- [ ] All 5 tracking files exist and are pre-filled per spec
