# TASK.md — Active Story: US-1.1

> Wiped and rewritten for US-1.1. Previous Sprint 0 tasks are in TRACK.md.

**Story:** US-1.1 — As a user, I can upload a CSV or Excel file so the platform can use it as a data source.
**Points:** 5 | **Sprint:** 1 | **Status:** In Progress

---

## Gherkin Acceptance Criteria (from prompt.md)
```
Given a user has a valid CSV file
When they upload it through the ingestion form
Then the file is parsed and loaded into raw_ingest
And a dataset_id is returned to the user

Given a user uploads a malformed or empty file
When the platform attempts to parse it
Then a clear, specific error message is shown
And nothing is written to the database
```

---

## Task Breakdown

### A — Shared infrastructure
- [x] `ingestion/logger.py` — structured JSON logger (shared across all pipeline stages)
- [x] `db/connection.py` — `get_engine()` using DATABASE_URL from env; `get_connection()` context manager

### B — Tests first (TDD)
- [x] `tests/test_file_ingestor.py` skeleton:
  - [x] `test_parse_csv_happy_path` — valid CSV → DataFrame with correct shape
  - [x] `test_parse_excel_happy_path` — valid .xlsx → DataFrame with correct shape
  - [x] `test_parse_csv_malformed` — bad CSV → IngestionError raised, nothing in DB
  - [x] `test_parse_csv_empty` — empty file → IngestionError raised, nothing in DB
  - [x] `test_ingest_file_returns_dataset_id` — valid CSV ingest → dataset_id string returned
  - [x] `test_ingest_file_writes_to_raw_ingest` — rows appear in raw_ingest after ingest

### C — Implementation
- [x] `ingestion/file_ingestor.py`:
  - [x] `class IngestionError(Exception)` — domain error for bad files
  - [x] `parse_csv(filepath: Path) -> pd.DataFrame`
  - [x] `parse_excel(filepath: Path) -> pd.DataFrame`
  - [x] `ingest_file(filepath: Path, source_name: str, conn) -> str` — returns dataset_id
  - [x] Structured logging: start / end / row_count / error at each step

### D — Verify & close
- [x] `pytest tests/test_file_ingestor.py -v` → all green
- [x] Coverage ≥ 70% on `ingestion/`
- [x] BACKLOG.md: US-1.1 → Done
- [x] TRACK.md entry appended
- [x] Git commit pushed
