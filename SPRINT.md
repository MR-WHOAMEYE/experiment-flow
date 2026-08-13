# SPRINT.md — Current Sprint

> **Rule:** Wipe and rewrite this file at the start of each new sprint. History lives in RETRO.md.

---

## Sprint 2 — External Connectors + Data Cleaning ✅ COMPLETE

| Field | Value |
|-------|-------|
| **Sprint Goal** | Users can connect API/PostgreSQL/MySQL sources; all ingested data is automatically cleaned before analysis. |
| **Start Date** | 2026-08-13 |
| **End Date** | 2026-08-13 |
| **Total Points** | 11 |
| **Git Tag** | `v0.2.0-sprint2` |

---

## Stories

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| US-1.2 | Connect API / PostgreSQL / MySQL source | 8 | ✅ Done |
| US-2.1 | Automatic data cleaning | 3 | ✅ Done |

---

## Story Checklist

### US-1.2 — External Connectors
- [x] `.env.example` updated with connector variables
- [x] `tests/test_connectors.py` — TDD unit tests (13 tests)
- [x] `ingestion/connectors/base.py` — `BaseConnector` ABC and `ConnectorError`
- [x] `ingestion/connectors/api_connector.py` — REST API data fetcher
- [x] `ingestion/connectors/postgres_connector.py` — PostgreSQL source connector
- [x] `ingestion/connectors/mysql_connector.py` — MySQL source connector
- [x] `test_connection()` implemented on each connector
- [x] 13/13 tests PASSED (mocked, no external DB needed)

### US-2.1 — Auto Data Cleaning
- [x] `tests/test_cleaner.py` — TDD unit tests (11 tests)
- [x] `cleaning/cleaner.py` — deduplication, HTML/emoji stripping, high-sparsity column drop, median/mode imputation
- [x] `CleaningReport` dataclass audit trail
- [x] 11/11 tests PASSED

---

## Sign-off
- [x] 45/45 total tests pass — `pytest`
- [x] Coverage: `ingestion/` & `cleaning/` **95%** (threshold: 70%)
- [x] Gherkin ACs verified
- [x] BACKLOG.md: US-1.2, US-2.1 → Done
- [x] TRACK.md entry appended
- [x] RETRO.md Sprint 2 entry written
- [x] Tag: `v0.2.0-sprint2`

_Sprint 2 closed. Next: Sprint 3 — DB & Query Optimization (US-3.1, 5 pts)_
