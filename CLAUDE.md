# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sherlock Homes is an SF real estate intelligence platform that matches users with property listings using NLP, geospatial analysis, and OpenAI Vision. It scores 17 weighted criteria per listing (natural light, outdoor space, character, tranquility, etc.) to surface what matters beyond basic inventory.

## Development Commands

```bash
# Local development (start both in separate terminals)
./run_local.sh      # API at :8000 (auto-creates venv, uses uv if available)
./run_frontend.sh   # Frontend at :5173

# Database
./nuke_db.sh && ./run_local.sh                    # Reset and restart
alembic upgrade head                              # Apply migrations
alembic revision --autogenerate -m "description"  # Create migration

# Testing
pytest tests/test_matching.py -v                  # Single file
pytest tests/test_matching.py::test_find_matches  # Single test

# Run visual analysis on existing listings
python -m app.scripts.analyze_visual_scores

# Docker (PostgreSQL-based)
make up && make logs    # Start services
make shell-db           # psql into database
make db-reset           # Nuke and recreate volumes

# Formatting
make fmt                # black + isort + prettier
```

## Architecture

### Scoring Engine (`services/advanced_matching.py`)
The `PropertyMatcher` class is the core intelligence layer:
1. Applies hard filters from `config/user_criteria.yaml` (price, beds, neighborhoods)
2. Runs NLP analysis on descriptions via `services/nlp.py`
3. Calculates 17 weighted scores (light, outdoor, character, kitchen, quiet location, etc.)
4. Applies soft-cap penalties (price, HOA) and generates match narratives
5. Returns tiered results: Exceptional (100+), Strong (88+), Interesting (76+), Pass

Scoring criteria weights and NLP signals are configured in `config/user_criteria.yaml` (path set via `BUYER_CRITERIA_PATH` env var).

### Provider System (`providers/`)
Multi-source ingestion with a registry pattern:
- `registry.py`: Maps source keys to provider classes, configured via `INGESTION_SOURCES` env var
- Providers: `zillow.py`, `redfin.py`, `trulia.py`, `realtor.py`, `craigslist.py`, `curated.py`
- All use ZenRows for scraping except Redfin (direct API with ZenRows fallback)

### Ingestion Pipeline (`services/ingestion.py`)
`run_ingestion_job()` orchestrates:
1. Fetches summaries from active providers (paginated, respects `MAX_PAGES`)
2. Enriches with detail calls (respects `MAX_DETAIL_CALLS`)
3. Extracts NLP flags, calculates tranquility/light scores
4. Upserts to DB, triggers alerts

### Frontend (`frontend/`)
Vite + React 18 with TypeScript. Key routes (via React Router):
- `/matches` - Scored listing feed with DossierCard components
- `/listings/:id` - Detail view with ImageGallery, feature scores
- `/criteria` - Buyer preference configuration

Data fetching uses React Query hooks in `src/hooks/`. API wrapper in `src/lib/api.ts`.

**Key directories:**
- `src/components/` - Reusable UI (cards, filters, gallery, layout, loading)
- `src/pages/` - Route components
- `src/hooks/` - React Query hooks (useMatches, useListings, useCriteria, useFeedback)
- `src/styles/` - CSS including design system tokens

Agentation toolbar enabled in dev mode for visual feedback.

### Data Flow
```
Providers → Ingestion → NLP/Geospatial Enrichment → DB
                                                    ↓
User Criteria (YAML) → PropertyMatcher → Scored Matches + Narratives
```

## Key Files to Understand

| File | Purpose |
|------|---------|
| `services/advanced_matching.py` | Scoring engine with 17 criteria, tier logic |
| `services/criteria_config.py` | Loads buyer criteria YAML, `BuyerCriteria` dataclass |
| `services/nlp.py` | Text signal extraction, light potential estimation |
| `services/geospatial.py` | Tranquility scoring from SF noise data |
| `providers/registry.py` | Provider factory pattern, source selection |
| `core/config.py` | Pydantic settings, all env vars documented |

## Configuration

Copy `.env.example` to `.env.local`:
```bash
# Required for data ingestion
ZENROWS_API_KEY=your_key
OPENAI_API_KEY=your_key  # For visual scoring + text intelligence

# Ingestion tuning
INGESTION_SOURCES=zillow           # Or: zillow,redfin,trulia
MAX_PAGES=25                        # Pages per source (~40 listings/page)
MAX_DETAIL_CALLS=200               # Detail enrichment limit

# Search filters (applied at source level)
SEARCH_PRICE_MIN=800000
SEARCH_BEDS_MIN=2
SEARCH_SQFT_MIN=1000

# Buyer criteria config
BUYER_CRITERIA_PATH=config/user_criteria.yaml
```

Python 3.11 or 3.12 required (spaCy wheel compatibility).

## Quick Verification

```bash
./run_local.sh
curl http://localhost:8000/health                       # API health
curl -X POST http://localhost:8000/admin/ingestion/run  # Trigger ingestion
curl http://localhost:8000/admin/ingestion/last-run     # Check status
curl http://localhost:8000/matches/test-user            # Get scored matches
```
