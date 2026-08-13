## 1. Project Context

Build an **End-to-End Experiment-as-a-Service (EaaS) Platform**: a self-service system where a user (technical or non-technical) provides a data source, and the platform runs data cleaning, EDA, A/B testing, ML prediction, and dashboarding on it — automatically, on a schedule.

**Core principle:** the A/B Testing Engine and ML Prediction Module must be *reusable* — driven by user-supplied config (which columns, which metric, which variants) — not hardcoded to one dataset or one comparison. That reusability is what makes this "a service" rather than a one-off script.

---

## 2. Tech Stack & Constraints

| Layer | Choice | Notes |
|---|---|---|
| Language | Python 3.11+ | Type hints required on all public functions |
| Database | PostgreSQL 15+ | No ORM abstraction over query-plan-relevant paths — raw SQL or SQLAlchemy Core (not full ORM) so `EXPLAIN ANALYZE` stays meaningful |
| Orchestration | n8n (self-hosted, Docker) | Workflows exported as JSON and version-controlled alongside code |
| ML | scikit-learn | No deep learning — capstone scope, needs to be explainable in a viva |
| Stats | SciPy / statsmodels | t-test, chi-square, and effect-size calculation |
| Frontend | Streamlit | Chosen over Flask for speed of a self-service form; swap-in for a production frontend documented as future work |
| Config | `.env` + `pydantic-settings` | No secrets committed; `.env.example` provided |
| Testing | `pytest` + `pytest-cov` | Minimum 70% coverage on non-UI code |
| Logging | Python `logging` module, structured (JSON) output | Every pipeline stage logs start/end/row-counts/errors |

**Explicitly out of scope** (document as future work, do not build): authentication/authorization, multi-tenancy, horizontal scaling, cloud deployment, rate limiting, billing.

---

## 3. Architecture Decisions (ADRs)

Record these as `docs/adr/NNN-title.md` files as you go. Seed ADRs:

- **ADR-001**: Use PostgreSQL upsert (`INSERT ... ON CONFLICT DO UPDATE`) for re-uploaded file sources, keyed on a per-source unique key, to avoid duplicate rows.
- **ADR-002**: A/B Testing Engine takes a config object (`{dataset, variant_column, metric_column, metric_type}`) rather than being written per-experiment — this is the reusability requirement, treat it as non-negotiable.
- **ADR-003**: Query-optimization benchmarks (EXPLAIN ANALYZE before/after) are stored in a `query_benchmarks` table, not just logged to console, so results survive past the session.
- Propose additional ADRs whenever you make a decision with more than one reasonable option (e.g., how retries are handled, how large files are chunked).

---

## 4. Data Model (starting point — refine as needed)

```sql
-- raw ingested data, one table per source, minimal transformation
CREATE TABLE raw_ingest (
    id BIGSERIAL PRIMARY KEY,
    source_type TEXT NOT NULL,       -- csv | excel | api | postgres | mysql | scrape
    source_name TEXT NOT NULL,
    ingested_at TIMESTAMPTZ DEFAULT now(),
    payload JSONB NOT NULL
);

-- cleaned, structured data ready for analysis
CREATE TABLE clean_records (
    id BIGSERIAL PRIMARY KEY,
    dataset_id TEXT NOT NULL,
    unique_key TEXT,                 -- for upsert de-duplication
    cleaned_at TIMESTAMPTZ DEFAULT now(),
    fields JSONB NOT NULL,
    UNIQUE (dataset_id, unique_key)
);

-- experiment configuration + results
CREATE TABLE experiments (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    dataset_id TEXT NOT NULL,
    variant_column TEXT NOT NULL,
    metric_column TEXT NOT NULL,
    metric_type TEXT NOT NULL,       -- numeric | categorical
    created_at TIMESTAMPTZ DEFAULT now(),
    p_value NUMERIC,
    lift_pct NUMERIC,
    significant BOOLEAN,
    status TEXT DEFAULT 'pending'    -- pending | running | complete | failed
);

-- ML prediction runs
CREATE TABLE predictions (
    id BIGSERIAL PRIMARY KEY,
    dataset_id TEXT NOT NULL,
    target_column TEXT NOT NULL,
    task_type TEXT NOT NULL,         -- regression | classification
    trained_at TIMESTAMPTZ DEFAULT now(),
    metric_name TEXT,                -- rmse | mae | f1 | accuracy
    metric_value NUMERIC,
    model_path TEXT                  -- serialized model location
);

-- query performance benchmarks
CREATE TABLE query_benchmarks (
    id BIGSERIAL PRIMARY KEY,
    query_label TEXT NOT NULL,
    before_ms NUMERIC,
    after_ms NUMERIC,
    before_plan_cost NUMERIC,
    after_plan_cost NUMERIC,
    recorded_at TIMESTAMPTZ DEFAULT now()
);
```

Treat this as a first draft — propose changes if your implementation needs them, but keep the reasoning visible in an ADR when you deviate.

---

## 5. Epics & User Stories (with story points and Gherkin acceptance criteria)

Story points are rough t-shirt-to-Fibonacci estimates (1/2/3/5/8) to help you sequence sprints — re-estimate if you disagree.

### Epic 1: Data Ingestion

**US-1.1** (5 pts) — As a user, I can upload a CSV or Excel file so the platform can use it as a data source.
```gherkin
Given a user has a valid CSV file
When they upload it through the ingestion form
Then the file is parsed and loaded into raw_ingest
And a dataset_id is returned to the user
Given a user uploads a malformed or empty file
When the platform attempts to parse it
Then a clear, specific error message is shown
And nothing is written to the database
```

**US-1.2** (8 pts) — As a user, I can connect an API, PostgreSQL, or MySQL source so the platform pulls data automatically.
```gherkin
Given a user provides connection credentials
When they click "Test Connection"
Then the platform confirms success or failure before saving
And credentials are stored encrypted, not in plain text
```

**US-1.3** (5 pts) — As a returning user, I can re-upload a file with new data without creating duplicate rows.
```gherkin
Given a dataset already has records with unique_key X
When a new file containing key X is uploaded again
Then the existing record is updated, not duplicated
And genuinely new keys are inserted as new rows
```

### Epic 2: Data Cleaning
**US-2.1** (3 pts) — As a user, my data is automatically cleaned before analysis runs.
```gherkin
Given raw data contains duplicates, HTML tags, and missing values
When the cleaning stage runs
Then duplicates are removed, HTML/emoji are stripped, and missing values are handled per a documented rule
And a cleaning report (rows affected, by type) is logged
```

### Epic 3: Database & Query Optimization
**US-3.1** (5 pts) — As a platform operator, common queries are indexed so performance doesn't degrade as data grows.
```gherkin
Given a query pattern used by 2+ pipeline stages
When indexing is applied
Then EXPLAIN ANALYZE shows reduced cost or execution time
And before/after results are stored in query_benchmarks
```

### Epic 4: A/B Testing Engine
**US-4.1** (8 pts) — As a user, I can define an experiment by choosing two variants and a success metric, without writing code.
```gherkin
Given a user selects a dataset, a variant column, and a metric column
When they submit the experiment config
Then the platform validates the columns exist and the metric type is inferred or confirmed
And the experiment is queued to run
```

**US-4.2** (5 pts) — As a user, I get a statistically valid result instead of raw counts.
```gherkin
Given an experiment has run to completion
When results are computed
Then the correct test (t-test for numeric, chi-square for categorical) is applied automatically
And the result includes p-value, significance flag, and % lift
```

### Epic 5: ML Prediction Module
**US-5.1** (8 pts) — As a user, I can choose a target column and get a trained model that predicts it.
```gherkin
Given a user selects a dataset and a target column
When they submit the prediction config
Then the platform infers regression vs. classification from the column type
And trains a model, reporting an appropriate accuracy metric
```

**US-5.2** (5 pts) — As a platform operator, the model retrains automatically when new data arrives.
```gherkin
Given new data has been ingested for a dataset with an existing model
When the scheduled n8n workflow runs
Then the model is retrained without manual intervention
And the new metric_value is compared against the previous run
```

### Epic 6: Dashboard
**US-6.1** (5 pts), **US-6.2** (3 pts) — descriptive stats + experiment/prediction results on one view. *(Write Gherkin for these yourself once the UI is scoped — flag back to me if the layout needs a decision.)*

### Epic 7: Automation (n8n)
**US-7.1** (5 pts) — As a platform operator, the full pipeline runs on a schedule without manual intervention.
```gherkin
Given a dataset has an active schedule
When the scheduled time arrives
Then n8n triggers ingest → clean → analyze → dashboard in sequence
And if any stage fails, an alert is sent and downstream stages do not run on stale data
```

### Epic 8: Self-Service Front End
**US-8.1** (8 pts), **US-8.2** (3 pts) — form-driven experiment creation, plain-language results.

---

## 6. Definition of Ready / Definition of Done

**A story is Ready when:** acceptance criteria are written in Gherkin, dependencies on other stories are identified, and the data it needs already exists (or ingestion for it is in an earlier sprint).

**A story is Done when:**
- Code is written and passes `pytest` with the stated coverage target
- Gherkin acceptance criteria are satisfied and demonstrable (via test or manual run)
- Logging is in place for the stage's start/end/failure
- Any new config/env var is documented in `.env.example`
- An ADR exists for any non-obvious decision made while building it

---


## 8. How I Want You  to Work

1. Propose a sprint plan sequencing the stories above by dependency (e.g., Epic 1 before Epic 4, since A/B testing needs ingested data). Include story points per sprint so the plan is scoped, not just ordered.
2. Confirm the plan with me before writing any code.
3. Set up the repo skeleton first: folder structure, `.env.example`, `requirements.txt`, `pytest` config, `docs/adr/` — as its own first sprint (Sprint 0).
4. Implement one sprint at a time, one story at a time within it, following the git workflow above.
5. After each story: show the diff, the test results, and update the ADR log if applicable. Wait for my confirmation before moving to the next story.
6. After each sprint: give me the sprint review + retrospective note described above.
7. Flag anything in section 2's "explicitly out of scope" list if a story seems to require it — don't quietly build it in.

