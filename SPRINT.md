# SPRINT.md — Current Sprint

> **Rule:** Wipe and rewrite this file at the start of each new sprint. History lives in RETRO.md.

---

## Sprint 6 — Dashboard + n8n Automation ✅ COMPLETE

| Field | Value |
|-------|-------|
| **Sprint Goal** | Interactive Streamlit dashboard displays descriptive stats, A/B experiment charts, ML metrics, and query benchmarks; automated end-to-end pipeline runner supports scheduled execution. |
| **Start Date** | 2026-08-13 |
| **End Date** | 2026-08-13 |
| **Total Points** | 13 |
| **Git Tag** | `v0.6.0-sprint6` |

---

## Stories

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| US-6.1 | Descriptive stats view | 5 | ✅ Done |
| US-6.2 | Experiment & prediction results view | 3 | ✅ Done |
| US-7.1 | Scheduled full pipeline (n8n cron / CLI runner) | 5 | ✅ Done |

---

## Story Checklist

### US-6.1 — Descriptive Stats Dashboard
- [x] `dashboard/stats.py` — `compute_summary_stats()` helper & Streamlit metrics view
- [x] `tests/test_dashboard_stats.py` — 2 unit tests for stats calculation & summary table formatting

### US-6.2 — Results Dashboard (Experiments & ML)
- [x] `dashboard/results.py` — A/B experiment charts, ML metrics display, and query benchmark plots
- [x] `dashboard/app.py` — Main Streamlit navigation app (Descriptive Stats, A/B Experiments, ML Predictions, Benchmarks)
- [x] `tests/test_dashboard_results.py` — 4 unit tests for DB data loading & Plotly figure generation

### US-7.1 — Automated Full Pipeline Runner
- [x] `scripts/run_pipeline.py` — CLI & n8n webhook runner executing Ingestion -> Cleaning -> Upsert -> A/B Experiment -> ML Retrain sequentially
- [x] `tests/test_pipeline_runner.py` — 1 unit test for full automated pipeline execution
- [x] 71/71 total tests PASSED | overall coverage: 93%

---

## Sign-off
- [x] 71/71 tests pass — `pytest`
- [x] Coverage: `dashboard/` **97%** (threshold: 70%)
- [x] Streamlit dashboard app ready (`streamlit run dashboard/app.py`)
- [x] BACKLOG.md: US-6.1, US-6.2, US-7.1 → Done
- [x] TRACK.md entry appended
- [x] RETRO.md Sprint 6 entry written
- [x] Tag: `v0.6.0-sprint6`

_Sprint 6 closed. Next: Sprint 7 — Self-Service Frontend (US-8.1, US-8.2, 11 pts)_
