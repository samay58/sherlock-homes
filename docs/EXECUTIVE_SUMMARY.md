# Sherlock Homes: Executive Summary

**Status**: Active development
**Last Updated**: February 22, 2026

## What It Does

Sherlock Homes ingests real estate listings, enriches them with multiple signals, and ranks matches against a buyer criteria config with explainable output.

Core signals:
- NLP keyword + signal extraction from description text
- Geospatial scoring (tranquility; SF-only today)
- Visual scoring via OpenAI Vision (optional; costs money)
- Change tracking (snapshots/events for price/status/photo changes)

## Current State

| Metric | Value |
|--------|-------|
| Listings | Varies with ingestion runs |
| Visual Scoring | Enabled when `OPENAI_API_KEY` is set and `VISUAL_SCORING_ENABLED=true` |
| Database | SQLite (local) or Postgres (Docker) |
| Match Output | Score + scorecard fields + top positives/tradeoff/why-now |

## Quick Start

```bash
# Start API
./run_local.sh

# Start frontend (separate terminal)
./run_frontend.sh

# Test
curl http://localhost:8000/matches/test-user | jq '.[0].address'
```

**API**: http://localhost:8000
**Frontend**: http://localhost:5173

## Local Data

- Local SQLite defaults to `sqlite:///./.local/sherlock.db` to avoid repo-root file sprawl.
- JSON exports default to `.local/data_export.json`.

## Architecture

```
./run_local.sh → uvicorn → FastAPI → SQLite

Scoring Pipeline:
  Listing → NLP Extract → Feature Flags → Weight × Score → Rank
               ↓
          Visual Scoring (OpenAI Vision, optional) → Bonus Points
               ↓
          Geospatial (Tranquility) → Location Adjustments
```

## Key Files

| File | Purpose |
|------|---------|
| `run_local.sh` | Start API with SQLite |
| `app/services/advanced_matching.py` | Scoring algorithm |
| `app/services/visual_scoring.py` | Visual scoring (OpenAI Vision) |
| `app/services/nlp.py` | Keyword extraction |
| `app/services/geospatial.py` | Tranquility scoring |
| `docs/archive/SESSION_PROGRESS.md` | Detailed history (archived) |

## Next Steps

1. **Fresh Ingestion**: Get current SF listings
   ```bash
   curl -X POST http://localhost:8000/admin/ingestion/run
   ```

2. **Score New Listings**: Auto-runs on new data
   ```bash
   python -m app.scripts.analyze_visual_scores
   ```

**Bottom Line**: Ingest, score, and iterate on criteria until the top of the list reliably contains the few listings worth acting on.
