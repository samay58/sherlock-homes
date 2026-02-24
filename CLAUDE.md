# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sherlock Homes is a real estate intelligence platform. The backend ingests listings from multiple providers (Zillow, StreetEasy, plus inactive adapters for Redfin, Trulia, Realtor, Craigslist), enriches them with NLP/geospatial/visual signals, and ranks matches against buyer criteria with explainable scoring. Currently configured for NYC rentals (`config/nyc_rental_criteria.yaml`); SF purchase config also available (`config/user_criteria.yaml`).

## Development Commands

```bash
# Local development (run in separate terminals)
./run_local.sh      # API at :8000 (bootstraps .venv, uses SQLite by default)
./run_frontend.sh   # Frontend at :5173 (Vite + React)

# Testing
make test                                    # All tests (prefers .venv when present)
.venv/bin/python -m pytest -q                 # All tests (explicit)
.venv/bin/python -m pytest tests/test_scoring.py -v            # Single file
.venv/bin/python -m pytest tests/test_scoring.py::test_name    # Single test

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
- **Sqft hard filter tolerates NULL**: The sqft_min hard filter passes listings with no sqft data; it only rejects listings with a known sqft below the minimum. This prevents dropping listings where the provider didn't report square footage.
- **Negation-aware detection**: Special `NEGATED_DOORMAN_PHRASES` list prevents "no doorman" counting as a doorman mention.
- **Context-dependent negatives**: "Flipper" negative only fires alongside `is_generic_description()` (short text < 80 words). "Dark" negatives suppressed if light positives present.
- **Weight learning** (`app/services/weight_learning.py`): Applies bounded multipliers (0.5x-2.0x) on top of YAML base weights. Requires minimum feedback (5 total, 3 likes, 2 dislikes) before adjusting.

### Ephemeral vs. Persisted Scores

This is the most non-obvious architectural decision. `PropertyListing` has both persisted columns (tranquility_score, light_potential_score, visual_quality_score set at ingestion time) and ephemeral attributes (match_score, score_tier, top_positives, key_tradeoff, signals, why_now) that `PropertyMatcher._apply_scorecard()` sets directly on the ORM object at read time. Scoring happens per-request, not at ingestion.

### Geospatial Intelligence

`app/services/geospatial.py`: Calculates tranquility scores (0-100) based on proximity to noise sources. Supports both SF and NYC with city auto-detection via bounding-box checks (`_is_in_sf`, `_is_in_nyc`). Returns `None` for coordinates outside both coverage areas.

NYC noise data covers:
- **8 busy streets**: Broadway, Canal, Houston, Bowery, Delancey, Flatbush Ave, Atlantic Ave, 4th Ave (Brooklyn)
- **2 freeways**: BQE (Brooklyn-Queens Expressway, severity 1.0), FDR Drive (severity 0.95)
- **8 FDNY stations**: DUMBO, Brooklyn Heights, Williamsburg, Fort Greene, East Village, SoHo, Chelsea, East Village/Gramercy

SF noise data covers 10 busy streets, 3 freeways (US-101, I-280, I-80), and 8 fire stations.

Convenience functions `is_on_busy_street()` and `is_near_freeway()` auto-select the correct city dataset.

### Ingestion Pipeline

`app/services/ingestion.py` orchestrates: provider iteration -> paginated summary fetch -> dedup by `(source, source_listing_id)` -> priority sort (in-budget first, then by photo count) -> detail enrichment (up to `MAX_DETAIL_CALLS=200`) -> NLP flag extraction -> geospatial scoring -> neighborhood normalization -> light potential estimation -> upsert with per-listing commits. Current stats: ~442 listings across ~20 neighborhoods, with ~36 matches returned.

Change detection works via `ListingSnapshot` diffing: snapshots capture (price, status, photos_hash, description_hash) at each ingestion, and events (price_drop, back_on_market, etc.) are derived from consecutive diffs.

Providers are registered in `app/providers/registry.py` as `ProviderSpec` objects. Most use ZenRows as a scraping proxy. The StreetEasy provider adds search filter params (price range, beds, baths) programmatically via `_with_search_filters()` using values from `SEARCH_PRICE_MIN`, `SEARCH_PRICE_MAX`, `SEARCH_BEDS_MIN`, and `SEARCH_BATHS_MIN` settings, so the configured neighborhood URLs stay clean.

### Text Intelligence Layer

`app/services/text_intelligence.py`: Optional LLM enrichment that runs at match time (`PropertyMatcher.find_matches`) on the top-N scored listings (default `OPENAI_TEXT_MAX_LISTINGS=5`). It uses the listing description plus a short event timeline to improve explainability fields (`top_positives`, `key_tradeoff`, `why_now`). Results are cached in-process by payload hash (no TTL; cache resets on process restart).

Provider selection:
- If `OPENAI_API_KEY` is set, call OpenAI first.
- If OpenAI fails or is unset and `DEEPINFRA_API_KEY` is set, fall back to DeepInfra (OpenAI-compatible endpoint).
- Disable entirely by setting `OPENAI_TEXT_MAX_LISTINGS=0`.

### Alert System

`app/services/listing_alerts.py` evaluates `ListingEvent`s (new_listing, price_drop, back_on_market, dom_stale) against buyer criteria and dispatches alerts via `app/services/alerts.py` (iMessage, email, SMS/Twilio, webhook).

Two-tier delivery for new listings: listings scoring above the immediate threshold (default 76%) trigger an immediate alert; listings that pass hard filters but score below 76% are sent to the digest instead. This means new listings always reach the digest if they clear hard filters, even if their score is not high enough for immediate notification.

Price drops follow a similar split: drops of 5%+ go immediate, 3-5% go to digest. Back-on-market events always go immediate. DOM stale events (45+ days) go to digest.

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
DEEPINFRA_API_KEY=...       # optional OpenAI-compatible fallback for text intelligence
DEEPINFRA_TEXT_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct
BUYER_CRITERIA_PATH=config/user_criteria.yaml    # SF (default) or config/nyc_rental_criteria.yaml
SEARCH_MODE=buy          # "buy" or "rent"
SEARCH_LOCATION=san-francisco-ca
INGESTION_SOURCES=zillow  # comma-separated: zillow,redfin,trulia,realtor,craigslist,streeteasy,curated
STREETEASY_SEARCH_URLS=   # comma-separated StreetEasy neighborhood URLs (only used when `streeteasy` is in INGESTION_SOURCES)
STREETEASY_MAX_PAGES=5    # cap StreetEasy pagination (in addition to global MAX_PAGES)

# Search filter params (used by Zillow URL builder + StreetEasy _with_search_filters)
SEARCH_PRICE_MIN=5000      # e.g. 5000 for NYC rent, 800000 for SF buy
SEARCH_PRICE_MAX=9500      # e.g. 9500 for NYC rent, empty for SF buy
SEARCH_BEDS_MIN=2
SEARCH_BATHS_MIN=2         # e.g. 2 for NYC rent, 1.5 for SF buy
SEARCH_SQFT_MIN=500
```

## Key Files

| File | Role |
|------|------|
| `config/user_criteria.yaml` | SF purchase scoring config |
| `config/nyc_rental_criteria.yaml` | NYC rental scoring config (active) |
| `app/services/advanced_matching.py` | Scoring engine (PropertyMatcher) |
| `app/services/scoring/primitives.py` | Score calculation helpers and dataclasses |
| `app/services/nlp.py` | Keyword extraction and flag detection |
| `app/services/geospatial.py` | Tranquility score from noise source proximity (SF + NYC) |
| `app/services/ingestion.py` | Ingestion orchestration |
| `app/services/persistence.py` | Upsert logic and change detection |
| `app/services/text_intelligence.py` | Optional LLM explainability enrichment (OpenAI, DeepInfra fallback) |
| `app/models/listing.py` | Central model (~60 columns, feature flags as booleans) |
| `app/models/listing_event.py` | Snapshot + event models for change tracking |
| `app/core/config.py` | All environment settings |
| `app/services/listing_alerts.py` | Alert evaluation: event-driven listing notifications (immediate + digest) |
| `app/services/alerts.py` | Alert delivery: iMessage, email, SMS/Twilio, webhook |
| `app/providers/streeteasy.py` | StreetEasy provider (ZenRows; NYC rentals; `_with_search_filters()` for param injection) |
