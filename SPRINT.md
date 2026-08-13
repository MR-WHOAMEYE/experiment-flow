# SPRINT.md — Current Sprint

> **Rule:** Wipe and rewrite this file at the start of each new sprint. History lives in RETRO.md.

---

## Sprint 1 — Data Ingestion (File Upload + Upsert) ✅ COMPLETE

| Field | Value |
|-------|-------|
| **Sprint Goal** | Users can upload CSV/Excel files; data lands in `raw_ingest`; re-uploads upsert cleanly with no duplicates. |
| **Start Date** | 2026-08-13 |
| **End Date** | 2026-08-13 |
| **Total Points** | 10 |
| **Git Tag** | `v0.1.0-sprint1` (commit `6ad224b`) |

---

## Stories

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| US-1.1 | Upload CSV / Excel file | 5 | ✅ Done |
| US-1.3 | Re-upload without duplicates (upsert) | 5 | ✅ Done |

---

## Story Checklist

### US-1.1
- [x] `ingestion/logger.py` — shared structured JSON logger
- [x] `db/connection.py` — `get_engine()` / `get_connection()` context manager
- [x] `tests/test_file_ingestor.py` — 13 tests written first (TDD)
- [x] `ingestion/file_ingestor.py` — `parse_csv`, `parse_excel`, `ingest_file`
- [x] 13/13 tests PASSED | coverage: ingestion/ 95%

### US-1.3
- [x] `tests/test_upsert.py` — 8 tests written first (TDD)
- [x] `upsert_to_clean_records()` in `file_ingestor.py`
- [x] 8/8 tests PASSED

---

## Sign-off
- [x] 21/21 tests pass — `pytest tests/test_file_ingestor.py tests/test_upsert.py -v`
- [x] Coverage: ingestion/ **95%** (threshold: 70%)
- [x] Gherkin ACs demonstrable via test names and assertions
- [x] BACKLOG.md: US-1.1, US-1.3 → Done
- [x] TRACK.md entry appended
- [x] RETRO.md Sprint 1 entry written
- [x] Tag: `v0.1.0-sprint1`

_Sprint 1 closed. Next: Sprint 2 — External Connectors + Data Cleaning (US-1.2, US-2.1, 11 pts)_
