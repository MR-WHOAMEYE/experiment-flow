# TASK.md — Active Story: US-1.2 & US-2.1

**Stories:** US-1.2 (External Connectors) & US-2.1 (Auto Data Cleaner)
**Sprint:** 2 | **Status:** ✅ Complete

---

## Task Breakdown

### US-1.2 — External Connectors (8 pts)
- [x] `tests/test_connectors.py` (13 tests):
  - [x] `test_api_connector_fetch_success`
  - [x] `test_api_connector_fetch_failure`
  - [x] `test_api_test_connection_success`
  - [x] `test_api_test_connection_failure`
  - [x] `test_postgres_connector_test_connection_success`
  - [x] `test_postgres_connector_test_connection_failure`
  - [x] `test_postgres_connector_fetch`
  - [x] `test_mysql_connector_test_connection_success`
  - [x] `test_mysql_connector_fetch`
- [x] `ingestion/connectors/base.py` — `BaseConnector` ABC + `ConnectorError`
- [x] `ingestion/connectors/api_connector.py` — REST API integration
- [x] `ingestion/connectors/postgres_connector.py` — SQLAlchemy Core PostgreSQL query connector
- [x] `ingestion/connectors/mysql_connector.py` — SQLAlchemy Core MySQL query connector

### US-2.1 — Auto Data Cleaning (3 pts)
- [x] `tests/test_cleaner.py` (11 tests):
  - [x] Exact duplicate row removal
  - [x] HTML tag & Emoji regex stripping
  - [x] >50% missing column dropping
  - [x] Numeric median & categorical mode imputation
- [x] `cleaning/cleaner.py` — `clean(df)` transformation & `CleaningReport` audit log
