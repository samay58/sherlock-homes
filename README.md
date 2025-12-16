# Sherlock Homes

An SF real estate matcher that actually thinks. It scores properties against your criteria using NLP, geospatial analysis, and Claude Vision photo scoring.

**The problem**: Zillow shows you what's for sale. It doesn't tell you what's worth your time.

**The solution**: Sherlock Homes analyzes 200+ signals per listing and ranks them by fit. It catches things humans miss: north-facing units, proximity to fire stations, staging that hides maintenance issues.

## Quick Start

```bash
# Start API
./run_local.sh

# Start frontend (separate terminal)
./run_frontend.sh
```

**API**: http://localhost:8000
**Frontend**: http://localhost:5173

## What It Does

**NLP Scoring**: Extracts 32+ keywords per feature category. Natural light, views, outdoor space, high ceilings, parking. Catches red flags too: busy streets, foundation issues, HOA problems.

**Visual Scoring**: Claude Vision analyzes listing photos. Rates modernity, condition, brightness, staging, and cleanliness. Flags water stains. Spots professional staging vs cluttered owner photos.

**Tranquility Score**: Calculates distance to busy streets, freeways, and fire stations. No external API needed. Uses static SF data and Haversine distance calculations.

**Light Potential**: Estimates natural light from description keywords. Top floor? Corner unit? South-facing? It tracks all of it. Penalizes north-facing and basement units.

**Vibe Presets**: Three personality modes. Light Chaser maximizes natural light and views. Urban Professional optimizes walkability. Deal Hunter prioritizes price drops and motivated sellers.

## How It Works

1. **Ingestion**: Pulls listings from Zillow via ZenRows. Runs every 6 hours.
2. **Enrichment**: Each listing gets NLP flags, geospatial scores, and visual analysis.
3. **Matching**: At query time, applies weighted multi-factor scoring against your criteria.
4. **Ranking**: Returns top matches with narratives explaining why each scored well.

## Architecture

```
sherlock-homes/
├── app/                    # FastAPI backend
│   ├── models/             # SQLAlchemy models
│   ├── services/
│   │   ├── nlp.py               # Keyword extraction
│   │   ├── advanced_matching.py # Scoring engine
│   │   ├── geospatial.py        # Tranquility calculations
│   │   └── visual_scoring.py    # Claude Vision
│   └── routes/             # API endpoints
├── frontend/               # SvelteKit app
├── scripts/                # Data tools
├── run_local.sh            # Start API
├── run_frontend.sh         # Start frontend
└── nuke_db.sh              # Reset database
```

## API Endpoints

| Endpoint | What it does |
|----------|--------------|
| `GET /matches/test-user` | Ranked matches with scores and narratives |
| `GET /listings` | All listings, paginated |
| `GET /listings/{id}` | Single listing detail |
| `POST /admin/ingestion/run` | Trigger data refresh |
| `GET /ping` | Health check |

## Development

**Reset database**:
```bash
./nuke_db.sh && ./run_local.sh
python scripts/import_from_json.py
```

**Run visual scoring**:
```bash
python -m app.scripts.analyze_visual_scores
```

## Configuration

Create `.env.local`:
```env
DATABASE_URL=sqlite:///./sherlock.db
ZENROWS_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
```

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Frontend**: SvelteKit, Svelte 5
- **Database**: SQLite (local), PostgreSQL (Docker)
- **AI**: Claude Vision for photo analysis

## License

MIT
