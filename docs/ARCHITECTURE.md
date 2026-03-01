# Architecture

## Overview

Sherlock Homes (repo: `home-hog`) is a FastAPI backend plus a Vite + React frontend.
It ingests listings from provider adapters, enriches them (NLP + geospatial + vision),
and computes per-request match scorecards against a buyer criteria YAML.

Production deployment and operational procedures live in `docs/OPERATIONS_FLY.md`.

## Repository Map

Backend (`app/`):

- `app/core/config.py`: Pydantic settings loaded from `.env` and `.env.local`
- `app/db/session.py`: SQLAlchemy engine/session (creates local SQLite parent dirs)
- `app/models/`: SQLAlchemy models (`PropertyListing`, `Criteria`, `User`, events/snapshots)
- `app/routes/`: FastAPI routers (`/listings`, `/matches`, `/criteria`, `/admin`, etc.)
- `app/services/`: ingestion, scoring/matching, NLP, alerts, persistence
- `app/providers/`: provider adapters (Zillow, Redfin, Trulia, Realtor, Craigslist, StreetEasy, curated)
- `app/schemas/`: Pydantic response models used by the API

Frontend (`frontend/`):

- `frontend/src/pages/`: route pages (matches, listings, criteria editor)
- `frontend/src/components/`: UI components (cards, filters, layout)
- `frontend/src/lib/api.ts`: fetch wrapper (defaults to relative URLs)
- `frontend/vite.config.ts`: dev proxy to the API (supports Docker via `VITE_API_TARGET`)

Other:

- `config/`: buyer criteria YAMLs and curated sources
- `migrations/` + `alembic.ini`: Alembic migrations (Postgres)
- `scripts/`: one-off import/export tools (JSON snapshot tooling)
- `docs/`: documentation (this folder)

## Data Flow

Ingestion:

1. Provider search summaries (`app/providers/*`)
2. Deduplicate by `(source, source_listing_id)`
3. Enrich details (bounded by `MAX_DETAIL_CALLS`)
4. Extract flags (NLP), compute cached intelligence (visual/geospatial), normalize neighborhoods
5. Upsert listings + snapshots/events (`app/services/persistence.py`)

Matching (read-time scoring):

1. Load criteria config (`app/services/criteria_config.py`)
2. Apply hard filters
3. Score weighted criteria (`app/services/advanced_matching.py` + `app/services/scoring/primitives.py`)
4. Attach explainability fields directly to the ORM object for API responses
5. Optional: run text intelligence (`app/services/text_intelligence.py`) on the top-N scored listings to improve explainability fields (OpenAI first, DeepInfra fallback)

## Storage

- Local dev: SQLite (default `sqlite:///./.local/sherlock.db`, with legacy detection for existing `./sherlock.db` or `./homehog.db`)
- Docker: Postgres (`DATABASE_URL=postgresql://...`, with `RUN_DB_MIGRATIONS_ON_STARTUP=true`)

## Key Constraints

- Providers should stay focused on fetching/parsing; scoring lives in `app/services/`
- Routes should remain thin; business logic belongs in services

## Configuration Notes

- Criteria config is selected via `BUYER_CRITERIA_PATH`:
  - SF default: `config/user_criteria.yaml`
  - NYC rentals: `config/nyc_rental_criteria.yaml`
- StreetEasy ingestion is enabled by including `streeteasy` in `INGESTION_SOURCES` and providing `STREETEASY_SEARCH_URLS` (comma-separated).
- StreetEasy pagination is capped by `STREETEASY_MAX_PAGES` (in addition to the global `MAX_PAGES` ingestion cap).
- Fly.io production keeps one warm machine (`min_machines_running=1`) so the in-process scheduler can execute recurring ingestion.
