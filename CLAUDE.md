# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sherlock Homes is a real estate intelligence platform. The backend ingests listings from multiple providers (Zillow, Redfin, Trulia, Realtor, Craigslist, StreetEasy), enriches them with NLP/geospatial/visual signals, and ranks matches against buyer criteria with explainable scoring. Currently SF-focused with NYC adaptation underway.

## Development Commands

```bash
# Local development (run in separate terminals)
./run_local.sh      # API at :8000 (bootstraps .venv, uses SQLite by default)
./run_frontend.sh   # Frontend at :5173 (Vite + React)

# Testing
pytest -q                                    # All tests
pytest tests/test_scoring.py -v              # Single file
pytest tests/test_scoring.py::test_name      # Single test

# Formatting and linting
make fmt             # black + isort (Python), npm run format (frontend)
make lint            # pylint (Python), npm run lint (frontend)

# Database reset
./nuke_db.sh

# Docker workflow
make up / make down / make dev / make logs
```

## Architecture

### Scoring Engine (the core)

The scoring system has three layers:

1. **Criteria config** (`app/services/criteria_config.py` + `config/user_criteria.yaml`): A frozen `BuyerCriteria` dataclass loaded once via `lru_cache(maxsize=1)`. The YAML defines hard filters (binary pass/fail), soft caps (penalty zones), weighted criteria (18 criteria across 3 tiers totaling 121 points), NLP signal keywords with multipliers, location modifiers, and explainability preferences.

2. **Scoring primitives** (`app/services/scoring/primitives.py`): Helper functions and the `ScoreComponent(score, weight, confidence, evidence)` dataclass. Each criterion produces one ScoreComponent with a 0-10 score. Key functions: `_score_from_hits()` (linear interpolation), `_soft_cap_penalty()`, `_hoa_penalty()` (step function), `_score_tier()` (maps percentage to Exceptional/Strong/Interesting/Pass).

3. **PropertyMatcher** (`app/services/advanced_matching.py`): Orchestrates scoring per-request. Two-pass hard filter: first pass checks DB columns (price, beds, baths, sqft, neighborhood), second pass checks NLP-derived signals (dark interior, busy street, low tranquility, layout red flags). Then scores 21 criteria independently, applies weighted total minus penalties, and attaches an explainability scorecard (top 3 positives, 1 key tradeoff, `why_now` timing insight).

Important scoring behaviors:
- **Buy vs. rent mode** (`SEARCH_MODE`): Parking is a hard filter only in buy mode; no-pets only in rent mode; HOA penalty skipped in rent mode.
- **Negation-aware detection**: Special `NEGATED_DOORMAN_PHRASES` list prevents "no doorman" counting as a doorman mention.
- **Context-dependent negatives**: "Flipper" negative only fires alongside `is_generic_description()` (short text < 80 words). "Dark" negatives suppressed if light positives present.
- **Weight learning** (`app/services/weight_learning.py`): Applies bounded multipliers (0.5x-2.0x) on top of YAML base weights. Requires minimum feedback (5 total, 3 likes, 2 dislikes) before adjusting.

### Ephemeral vs. Persisted Scores

This is the most non-obvious architectural decision. `PropertyListing` has both persisted columns (tranquility_score, light_potential_score, visual_quality_score set at ingestion time) and ephemeral attributes (match_score, score_tier, top_positives, key_tradeoff, signals, why_now) that `PropertyMatcher._apply_scorecard()` sets directly on the ORM object at read time. Scoring happens per-request, not at ingestion.

### Ingestion Pipeline

`app/services/ingestion.py` orchestrates: provider iteration -> paginated summary fetch -> dedup by `(source, source_listing_id)` -> priority sort (in-budget first, then by photo count) -> detail enrichment (up to `MAX_DETAIL_CALLS=200`) -> NLP flag extraction -> geospatial scoring -> neighborhood normalization -> light potential estimation -> upsert with per-listing commits.

Change detection works via `ListingSnapshot` diffing: snapshots capture (price, status, photos_hash, description_hash) at each ingestion, and events (price_drop, back_on_market, etc.) are derived from consecutive diffs.

Providers are registered in `app/providers/registry.py` as `ProviderSpec` objects. Most use ZenRows as a scraping proxy.

### Text Intelligence Layer

`app/services/text_intelligence.py`: Optional OpenAI-powered enrichment that runs on top-N scored listings (default 5). Sends description + event timeline to GPT-4o-mini and can override NLP-derived explainability fields. Results cached in-memory by content hash.

### State Management

Minimal: a single Pydantic `BaseModel` instance at module scope in `app/state.py` tracks ingestion job metrics. Everything else flows through the SQLAlchemy session (dependency-injected via `get_db()`) or the `BuyerCriteria` singleton.

### Frontend

Vite + React 18 + TypeScript + TanStack React Query + React Router. Five routes: `/` (landing), `/matches` (primary results with vibe presets, quick filters, sort options), `/listings` (raw browser), `/listings/:id` (detail), `/criteria` (editor). Design system: Rauno Freiberg-inspired minimal CSS (`sherlock-tokens.css`, `rauno-minimal.css`, `rauno-effects.css`).

API client in `frontend/src/lib/api.ts` is a thin fetch wrapper. Types in `frontend/src/lib/types.ts` mirror the backend model.

## Testing Patterns

Tests use a file-based SQLite test DB (defaults to `.local/test.db`) with `conftest.py` providing `db_session`, `test_user`, and `client` fixtures. Scoring tests create `PropertyListing` objects, construct a `PropertyMatcher`, call `score_listing()`, and assert on attached attributes. Test-specific YAML configs are managed by patching `settings.BUYER_CRITERIA_PATH` and clearing the `lru_cache`.

When tests need custom criteria, use the `_configure_criteria` / `_restore_criteria` pattern from `test_scoring.py`.

## Configuration

Environment loaded from `.env` and `.env.local` (local overrides) via Pydantic `BaseSettings` in `app/core/config.py`.

```env
DATABASE_URL=sqlite:///./.local/sherlock.db
ZENROWS_API_KEY=...
OPENAI_API_KEY=...
SEARCH_MODE=buy          # "buy" or "rent"
SEARCH_LOCATION=san-francisco-ca
INGESTION_SOURCES=zillow  # comma-separated: zillow,redfin,trulia,realtor,craigslist,streeteasy,curated
STREETEASY_SEARCH_URLS=   # comma-separated StreetEasy neighborhood URLs (only used when `streeteasy` is in INGESTION_SOURCES)
```

## Key Files

| File | Role |
|------|------|
| `config/user_criteria.yaml` | All scoring weights, filters, NLP keywords, location modifiers |
| `app/services/advanced_matching.py` | Scoring engine (PropertyMatcher) |
| `app/services/scoring/primitives.py` | Score calculation helpers and dataclasses |
| `app/services/nlp.py` | Keyword extraction and flag detection |
| `app/services/geospatial.py` | Tranquility score from SF noise source proximity |
| `app/services/ingestion.py` | Ingestion orchestration |
| `app/services/persistence.py` | Upsert logic and change detection |
| `app/models/listing.py` | Central model (~60 columns, feature flags as booleans) |
| `app/models/listing_event.py` | Snapshot + event models for change tracking |
| `app/core/config.py` | All environment settings |
