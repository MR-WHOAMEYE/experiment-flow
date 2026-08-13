# EaaS — Experiment-as-a-Service Platform

A self-service platform where a user provides a data source and the platform runs
**data cleaning → EDA → A/B testing → ML prediction → dashboarding** automatically, on a schedule.

> Capstone project. Tech stack: Python 3.11 · PostgreSQL 15 · scikit-learn · SciPy · Streamlit · n8n (Docker).

---

## Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ running locally
- Docker (for n8n)
- Git

### 1 — Clone & configure

```bash
git clone <repo-url>
cd "QP CAPSTONE"
cp .env.example .env
# Edit .env with your local PostgreSQL credentials
```

### 2 — Create virtual environment & install dependencies

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3 — Apply the database schema

```bash
psql -U <your_pg_user> -d <your_db_name> -f db/migrations/001_initial_schema.sql
```

Verify with:
```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = ''public'' ORDER BY table_name;
-- Expected: clean_records, experiments, predictions, query_benchmarks, raw_ingest
```

### 4 — Run tests

```bash
pytest
# With coverage (enforced ≥70% on non-UI code):
pytest --cov=. --cov-report=term-missing --cov-fail-under=70
```

### 5 — Start the Streamlit dashboard

```bash
streamlit run dashboard/app.py
```

### 6 — Start n8n (Docker)

```bash
docker run -d --name n8n -p 5678:5678 \
  -e N8N_BASIC_AUTH_ACTIVE=false \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n
# Open http://localhost:5678 and import automation/n8n_workflows/pipeline.json
```

---

## Project Structure

```
QP CAPSTONE/
├── ingestion/           # File + connector ingestion (US-1.1, US-1.2, US-1.3)
│   └── connectors/      # API, PostgreSQL, MySQL connectors
├── cleaning/            # Auto data cleaning pipeline (US-2.1)
├── ab_testing/          # A/B testing engine — config + stats (US-4.1, US-4.2)
├── ml/                  # ML training + auto-retraining (US-5.1, US-5.2)
├── dashboard/           # Streamlit dashboard (US-6.1, US-6.2, US-8.1, US-8.2)
├── automation/
│   └── n8n_workflows/   # n8n pipeline JSON (US-7.1)
├── db/
│   └── migrations/      # SQL migration files (run in order)
├── docs/
│   └── adr/             # Architecture Decision Records
├── models/              # Serialized ML model files (.pkl) — gitignored
├── tests/               # pytest test suite
├── .env.example         # Required env vars (copy to .env)
├── requirements.txt     # Pinned Python dependencies
├── pytest.ini           # Test configuration
├── BACKLOG.md           # Full product backlog with status tracking
├── SPRINT.md            # Current sprint plan
├── TASK.md              # Active story task breakdown (scratchpad)
├── TRACK.md             # Append-only dev log
└── RETRO.md             # Sprint retrospectives
```

---

## Tracking Files

| File | Purpose |
|------|---------|
| `BACKLOG.md` | All epics/stories/points — update when status changes |
| `SPRINT.md` | Current sprint only — rewritten each sprint |
| `TASK.md` | Active story task breakdown — wiped per story |
| `TRACK.md` | Append-only dev log — never delete entries |
| `RETRO.md` | One entry per completed sprint — never delete entries |

---

## Architecture Decisions

See `docs/adr/` for all ADRs:
- [ADR-001](docs/adr/001-postgres-upsert.md) — PostgreSQL upsert for re-uploaded files
- [ADR-002](docs/adr/002-ab-config-object.md) — Config-driven A/B testing engine
- [ADR-003](docs/adr/003-query-benchmarks-table.md) — Query benchmarks stored in DB

---

## Known Limitations / Future Work

The following are **explicitly out of scope** for this capstone and documented as future work:
- Authentication / authorization
- Multi-tenancy
- Horizontal scaling
- Cloud deployment (AWS/GCP/Azure)
- Rate limiting
- Billing

---

## Known Caveats

- **Upsert key column**: When re-uploading a file, the schema (column names) must match the original upload. Adding/removing columns between uploads may cause unexpected upsert behaviour — see ADR-001.
- **PostgreSQL version sensitivity**: `EXPLAIN ANALYZE` output parsing in `db/benchmark.py` is tested against PostgreSQL 15. Output format differs in earlier versions.
