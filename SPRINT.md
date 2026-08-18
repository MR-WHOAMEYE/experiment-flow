# SPRINT.md — Current Sprint

> **Rule:** Wipe and rewrite this file at the start of each new sprint. History lives in RETRO.md.

---

## Sprint 7 — Self-Service Frontend ✅ COMPLETE & PROJECT SIGN-OFF

| Field | Value |
|-------|-------|
| **Sprint Goal** | Form-driven experiment & ML model creation in Streamlit dashboard with plain-language natural language summaries for non-technical users. |
| **Start Date** | 2026-08-13 |
| **End Date** | 2026-08-13 |
| **Total Points** | 11 |
| **Git Tag** | `v1.0.0-final` |

---

## Stories

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| US-8.1 | Form-driven experiment creation | 8 | ✅ Done |
| US-8.2 | Plain-language results summary | 3 | ✅ Done |

---

## Story Checklist

### US-8.1 — Form-Driven Creation
- [x] Streamlit form in `dashboard/app.py` for interactive A/B experiment creation
- [x] Streamlit form in `dashboard/app.py` for interactive ML model training
- [x] `tests/test_dashboard_forms.py` — 1 unit test for interactive creation logic

### US-8.2 — Plain-Language Narrative Summary
- [x] `dashboard/narrative.py` — `generate_ab_narrative()` and `generate_ml_narrative()`
- [x] Integrated plain-language text cards into `dashboard/app.py`
- [x] `tests/test_narrative.py` — 4 unit tests for narrative generation
- [x] 76/76 total tests PASSED | overall coverage: 80%

---

## Final Project Sign-off
- [x] All 15 User Stories (US-1.1 through US-8.2) completed (81 total story points)
- [x] 76/76 unit tests pass — `pytest`
- [x] Live Neon PostgreSQL Database connected & schema migrated
- [x] DB EXPLAIN ANALYZE index optimization verified (263.62x speedup)
- [x] Final Tag: `v1.0.0-final`

---

## Sprint 8 — Post-Release Extension: Web Scraping ✅ COMPLETE

| Field | Value |
|-------|-------|
| **Sprint Goal** | Add `FirecrawlConnector` (web scraping) as a new ingestion source that plugs into the existing `raw_ingest` pipeline, with full offline test coverage. |
| **Start Date** | 2026-08-18 |
| **End Date** | 2026-08-18 |
| **Total Points** | 3 |
| **Git Tag** | `455a94e` (post-v1.0.0-final) |

## Stories

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| US-1.4 | Firecrawl web scraping connector | 3 | ✅ Done |

## Story Checklist

### US-1.4 — Firecrawl Web Scraping Connector
- [x] `ingestion/connectors/firecrawl_connector.py` — `FirecrawlConnector(BaseConnector)` implementing:
  - [x] `fetch(url)` — single-page scrape via POST `/v1/scrape`
  - [x] `fetch(url, crawl=True, limit=N)` — async site crawl via POST `/v1/crawl` with polling
  - [x] Output: `DataFrame(url, title, content, scraped_at)` → `raw_ingest` pipeline
  - [x] `FIRECRAWL_API_KEY` / `FIRECRAWL_BASE_URL` env var support (self-hosted & cloud)
- [x] `tests/test_firecrawl_connector.py` — 17 offline tests (all HTTP mocked via `responses`)
  - [x] Construction & env-var key discovery (5 tests)
  - [x] `test_connection()` — 2xx success, HTTP error, connection error (3 tests)
  - [x] Single-page `fetch()` — columns, row count, content, error cases (5 tests)
  - [x] Crawl-mode `fetch()` — multi-row output, submit failure, failed status, missing ID (4 tests)
- [x] `requirements.txt` — `firecrawl-py==1.7.0` added
- [x] `.env` — `FIRECRAWL_API_KEY` placeholder + `FIRECRAWL_BASE_URL` comment added
- [x] **17/17 tests PASSED** | committed `455a94e`

---

## Sprint 9 — Full UI Redesign (5-Page Multi-Page App) 🚧 IN PROGRESS

| Field | Value |
|-------|-------|
| **Sprint Goal** | Replace the single-file sidebar dashboard with a premium 5-page Streamlit multi-page app: Home, Create Experiment wizard, Results Dashboard, Experiment History, and Settings. No technical jargon in any user-facing copy. |
| **Start Date** | 2026-08-18 |
| **Target End Date** | 2026-08-18 |
| **Total Points** | 20 |
| **Git Tag** | TBD |

## Stories

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| US-9.1 | Home page — hero, CTA, recent experiments table | 3 | 🔲 Not Started |
| US-9.2 | Create Experiment — 4-step wizard | 8 | 🔲 Not Started |
| US-9.3 | Results Dashboard — verdict, charts, diagnostics | 5 | 🔲 Not Started |
| US-9.4 | Experiment History — search, pagination, clone | 3 | 🔲 Not Started |
| US-9.5 | Settings page — placeholder | 1 | 🔲 Not Started |

## Story Checklist

### US-9.1 — Home Page
- [ ] `dashboard/pages/home.py` — hero section with animated gradient, headline, CTA button
- [ ] Recent experiments table (5 most recent from DB, with ID/type/status badges)
- [ ] CTA "Create New Experiment" navigates to Create Experiment page

### US-9.2 — Create Experiment Wizard
- [ ] `dashboard/pages/create_experiment.py` — 4-step wizard via `st.session_state["wizard"]`
- [ ] Step 1: Data source radio (CSV / Excel / PostgreSQL / MySQL / API / Firecrawl URL) with conditional upload/form widgets
- [ ] Step 2: Analysis type radio (EDA only / A/B Testing / ML Prediction / All)
- [ ] Step 3: Configure (conditional — skipped for EDA-only; A/B dropdowns; ML target dropdown)
- [ ] Step 4: Review summary → "Create Experiment" button → execute backend → show narrative inline
- [ ] Progress bar showing current step (1/4 → 4/4)
- [ ] Back/Next/Cancel navigation at each step

### US-9.3 — Results Dashboard
- [ ] `dashboard/pages/results_dashboard.py` — loads experiment by name from session state
- [ ] Plain-language verdict header (✓ Significant / ✗ Not Significant) with large icon
- [ ] Plotly box/violin distribution chart (side-by-side per variant)
- [ ] Diagnostics section: sample sizes, test type, effect size, p-value (rounded)
- [ ] ML results variant: feature importance bar chart, accuracy/RMSE summary

### US-9.4 — Experiment History
- [ ] `dashboard/pages/history.py` — full experiment table from DB
- [ ] Search input filters rows by experiment name in real-time
- [ ] Manual pagination (10 rows/page, Prev/Next buttons via session_state)
- [ ] Row "View" button sets `st.session_state["view_experiment"]` and navigates to Results
- [ ] Row "Clone" button copies experiment config to wizard session state

### US-9.5 — Settings (Placeholder)
- [ ] `dashboard/pages/settings.py` — static markdown with future config items

### Global / App Shell
- [ ] `dashboard/pages/__init__.py` — package marker
- [ ] `dashboard/app.py` refactored to use `st.navigation()` + `st.Page()` API
- [ ] Global CSS injected: dark navy background, Inter font, glassmorphism cards
- [ ] `sys.path` fix kept in `app.py` entry point (single place)
- [ ] All 93 existing tests continue to pass


