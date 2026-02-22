# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sherlock Homes is an SF real estate intelligence platform. The backend ingests listings from multiple providers, enriches them with NLP/geospatial/visual signals, and ranks matches against buyer criteria with explainable scoring.

## Development Commands

```bash
# Local development (run in separate terminals)
./run_local.sh      # API at :8000 (bootstraps .venv/venv, uses SQLite by default)
./run_frontend.sh   # Frontend at :5173 (Vite + React)

# Testing
pytest -q
pytest tests/test_matching.py -v
pytest tests/test_matching.py::test_find_matches

# Formatting and linting
make fmt
make lint

# Database and migrations
./nuke_db.sh
alembic upgrade head
alembic revision --autogenerate -m "description"

# Ingestion and analysis
python -m app.scripts.analyze_visual_scores
python scripts/import_from_json.py

# Docker workflow
make up
make dev
make logs
make shell-db
```

## Architecture

### Backend (`app/`)

- FastAPI app entrypoint: `app/main.py`
- Routers:
  - `app/routes/admin.py`
  - `app/routes/listings.py`
  - `app/routes/criteria.py`
  - `app/routes/feedback.py`
  - `app/routes/scouts.py`
  - `app/routes/users.py`
- Models: `app/models/`
- Schemas: `app/schemas/`
- Services: `app/services/`
- Providers: `app/providers/`

Startup behavior:
- SQLite: auto-creates tables from SQLAlchemy models.
- PostgreSQL: can run Alembic migrations on startup when enabled.
- Ensures a default test user exists.
- Starts scheduled ingestion when `ZENROWS_API_KEY` and auto-ingestion are enabled.

### Matching and Scoring

- Core engine: `app/services/advanced_matching.py` (`PropertyMatcher`)
- Criteria config: `app/services/criteria_config.py` + `config/user_criteria.yaml`
- NLP and light estimation: `app/services/nlp.py`
- Geospatial tranquility/location modifiers: `app/services/geospatial.py`
- Optional text intelligence enrichment: `app/services/text_intelligence.py`
- Visual scoring pipeline: `app/services/visual_scoring.py`
- Learned preference weights: `app/services/weight_learning.py`

### Ingestion Pipeline

- Orchestration: `app/services/ingestion.py`
- Provider registry: `app/providers/registry.py`
- Providers include Zillow, Redfin, Trulia, Realtor, Craigslist, and curated sources.
- Endpoints:
  - `POST /admin/ingestion/run`
  - `GET /admin/ingestion/last-run`
  - `GET /ingestion/status`

### Frontend (`frontend/`)

- Stack: Vite + React 18 + TypeScript + React Query + React Router.
- Entry: `frontend/src/main.tsx`
- Routes/pages: `frontend/src/pages/`
- Shared components: `frontend/src/components/`
- Data hooks: `frontend/src/hooks/`
- API helpers + types: `frontend/src/lib/`
- Styling: `frontend/src/styles/`

## Key Endpoints

- `GET /ping`
- `GET /matches/test-user`
- `GET /matches/user/{user_id}`
- `GET /listings`
- `GET /listings/{id}`
- `GET /listings/{id}/history`
- `GET /changes`
- `GET /criteria/test-user`
- `POST /criteria/test-user`
- `POST /feedback/{listing_id}`
- `GET /users/{user_id}/weights`
- `POST /users/{user_id}/weights/recalculate`
- `POST /admin/ingestion/run`
- `GET /admin/ingestion/last-run`

## Configuration

Environment is loaded from `.env` and `.env.local` (local overrides).

Common local settings:

```env
DATABASE_URL=sqlite:///./homehog.db
ZENROWS_API_KEY=...
OPENAI_API_KEY=...
# Optional legacy key:
ANTHROPIC_API_KEY=...
```

Useful tuning variables:
- `INGESTION_SOURCES`
- `MAX_PAGES`
- `MAX_DETAIL_CALLS`
- `SEARCH_LOCATION` / `SEARCH_LOCATIONS`
- `SEARCH_MODE` (`buy` or `rent`)
- `BUYER_CRITERIA_PATH`

Python 3.11 or 3.12 is recommended.

## Quick Verification

```bash
./run_local.sh
curl http://localhost:8000/ping
curl -X POST http://localhost:8000/admin/ingestion/run
curl http://localhost:8000/admin/ingestion/last-run
curl http://localhost:8000/matches/test-user
```
