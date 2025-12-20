# Sherlock Homes: Executive Summary

**Status**: Fully Operational
**Last Updated**: December 20, 2025

## What It Does

Intelligent SF real estate matcher that scores properties against your criteria using:
- NLP keyword extraction (natural light, views, outdoor space, etc.)
- Multi-factor scoring (0-100 scale with 13+ weighted features)
- Claude Vision photo analysis (visual quality scoring)
- Geospatial intelligence (Tranquility Score for noise exposure)
- Explicit match explanations (why it matched + one tradeoff)

## Current State

| Metric | Value |
|--------|-------|
| Listings | Varies with ingestion runs |
| Visual Scoring | Enabled when `ANTHROPIC_API_KEY` set |
| Database | SQLite (local) or PostgreSQL (Docker) |
| Match Output | Scores + reasons + tradeoff |

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

## Scoring System

### Multi-Factor Weights
| Feature | Weight | Source |
|---------|--------|--------|
| Natural Light | 10 | NLP |
| View | 9 | NLP |
| Visual Quality | 8 | Claude Vision |
| Outdoor Space | 8 | NLP |
| Updated Systems | 7 | NLP |
| High Ceilings | 7 | NLP |

### Visual Scoring
- Claude Vision analyzes first 3 photos per listing
- Evaluates: modernity, condition, brightness, staging, cleanliness
- Cost: ~$0.008/listing ($0.32 for 41 listings)
- Cached via photo hash. Only re-analyzes when photos change.

## Architecture

```
./run_local.sh → uvicorn → FastAPI → SQLite

Scoring Pipeline:
  Listing → NLP Extract → Feature Flags → Weight × Score → Rank
               ↓
          Visual Scoring (Claude Vision) → Bonus Points
               ↓
          Geospatial (Tranquility) → Location Adjustments
```

## Key Files

| File | Purpose |
|------|---------|
| `run_local.sh` | Start API with SQLite |
| `app/services/advanced_matching.py` | Scoring algorithm |
| `app/services/visual_scoring.py` | Claude Vision |
| `app/services/nlp.py` | Keyword extraction |
| `app/services/geospatial.py` | Tranquility scoring |
| `SESSION_PROGRESS.md` | Detailed history |

## Next Steps

1. **Fresh Ingestion**: Get current SF listings
   ```bash
   curl -X POST http://localhost:8000/admin/ingestion/run
   ```

2. **Score New Listings**: Auto-runs on new data
   ```bash
   python -m app.scripts.analyze_visual_scores
   ```

**Bottom Line**: System is fully operational with visual scoring active. Ready for fresh data.
