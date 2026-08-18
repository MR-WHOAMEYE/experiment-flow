# EaaS Platform — Product Backlog

> Mirrors `prompt.md §5`. Update the **Status** column whenever a story changes state.
> Statuses: `Not Started` | `In Progress` | `Blocked` | `Done`

---

## Epic 1 — Data Ingestion

| Story | Title | Points | Status | Notes |
|-------|-------|--------|--------|-------|
| US-1.1 | Upload CSV / Excel file | 5 | Done | |
| US-1.2 | Connect API / PostgreSQL / MySQL source | 8 | Done | |
| US-1.3 | Re-upload without creating duplicates (upsert) | 5 | Done | Depends on US-1.1 |
| US-1.4 | Firecrawl web scraping connector | 3 | Done | Extends US-1.2; single-page + async site crawl |

---

## Epic 2 — Data Cleaning

| Story | Title | Points | Status | Notes |
|-------|-------|--------|--------|-------|
| US-2.1 | Automatic data cleaning before analysis | 3 | Done | Depends on US-1.1 |

---

## Epic 3 — Database & Query Optimization

| Story | Title | Points | Status | Notes |
|-------|-------|--------|--------|-------|
| US-3.1 | Index common queries; benchmark before/after | 5 | Done | Depends on US-2.1 |

---

## Epic 4 — A/B Testing Engine

| Story | Title | Points | Status | Notes |
|-------|-------|--------|--------|-------|
| US-4.1 | Define experiment config (no-code) | 8 | Done | Depends on US-2.1 |
| US-4.2 | Compute statistically valid results | 5 | Done | Depends on US-4.1 |

---

## Epic 5 — ML Prediction Module

| Story | Title | Points | Status | Notes |
|-------|-------|--------|--------|-------|
| US-5.1 | Train model on user-selected target column | 8 | Done | Depends on US-2.1 |
| US-5.2 | Auto-retrain model when new data arrives | 5 | Done | Depends on US-5.1, US-7.1 |

---

## Epic 6 — Dashboard

| Story | Title | Points | Status | Notes |
|-------|-------|--------|--------|-------|
| US-6.1 | Descriptive stats view | 5 | Done | Depends on US-2.1 |
| US-6.2 | Experiment & prediction results view | 3 | Done | Depends on US-4.2, US-5.1 |

---

## Epic 7 — Automation (n8n)

| Story | Title | Points | Status | Notes |
|-------|-------|--------|--------|-------|
| US-7.1 | Scheduled full pipeline (n8n cron) | 5 | Done | Depends on US-2.1, US-4.2, US-5.1 |

---

## Epic 8 — Self-Service Frontend

| Story | Title | Points | Status | Notes |
|-------|-------|--------|--------|-------|
| US-8.1 | Form-driven experiment creation | 8 | Done | Depends on US-4.1, US-6.1 |
| US-8.2 | Plain-language results summary | 3 | Done | Depends on US-4.2, US-8.1 |

---

## Post-Release Extensions (Sprint 8 — after v1.0.0-final)

| Story | Title | Points | Status | Notes |
|-------|-------|--------|--------|-------|
| US-1.4 | Firecrawl web scraping connector | 3 | Done | `ingestion/connectors/firecrawl_connector.py`; 17/17 tests |

---

## Sprint Allocation Summary

| Sprint | Stories | Points | Theme |
|--------|---------|--------|-------|
| Sprint 0 | (infra) | ~5 | Repo skeleton, schema, ADR seeds, tracking files |
| Sprint 1 | US-1.1, US-1.3 | 10 | File ingestion + upsert |
| Sprint 2 | US-1.2, US-2.1 | 11 | External connectors + cleaning |
| Sprint 3 | US-3.1 | 5 | DB indexing + benchmarks |
| Sprint 4 | US-4.1, US-4.2 | 13 | A/B testing engine |
| Sprint 5 | US-5.1, US-5.2 | 13 | ML prediction + auto-retrain |
| Sprint 6 | US-6.1, US-6.2, US-7.1 | 13 | Dashboard + n8n automation |
| Sprint 7 | US-8.1, US-8.2 | 11 | Self-service frontend |
| Sprint 8 | US-1.4 | 3 | Post-release: Firecrawl web scraping |
| **Total** | | **~84 pts** | |


