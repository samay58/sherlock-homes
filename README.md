# Sherlock Homes

SF real estate is a nightmare. This makes it slightly less of one.

Sherlock Homes ranks listings against your criteria using NLP, geospatial signals, and Claude Vision. Because staring at 47 identical "sun-drenched" listings should not be a full-time job.

## The Problem

Zillow tells you what exists. It does not tell you what is good. The north-facing "garden unit" with the $15k/year HOA and a fire station next door? Zillow will show it. We will not.

Sherlock Homes reviews 200+ signals per listing so you do not learn the obvious after a 40-minute drive.

## Quick Start

```bash
# Start API
./run_local.sh

# Start frontend (separate terminal)
./run_frontend.sh
```

API: http://localhost:8000
Frontend: http://localhost:5173

Python 3.11/3.12 recommended. If `uv` is installed, `./run_local.sh` will use it automatically.

## What It Actually Does

**NLP Scoring**
Reads descriptions like a suspicious buyer. Extracts 32+ keywords across categories: natural light, views, outdoor space, high ceilings, parking. Flags the bad stuff too. "Cozy" usually means small.

**Visual Scoring**
Claude Vision looks at listing photos. Rates modernity, condition, brightness, staging, cleanliness. Catches water stains, tired fixtures, and the telltale signs of a flipper who watched too much HGTV.

**Tranquility Score**
How close is this place to things that make noise? Freeways, busy streets, fire stations. No API calls. Just local SF data and geometry. Some of us have meetings.

**Light Potential**
Estimates how much natural light you will actually get. Top floor, corner unit, south-facing equals good. North-facing basement equals lamps.

**Why This Matched**
Every match includes explicit reasons (budget fit, neighborhood focus, recency, light, quiet) plus one tradeoff. No black-box scores.

**Change Tracking**
Detects meaningful listing changes like price drops, status flips, and photo updates so you do not miss the quiet gems.

## Vibe Presets

- **Light Chaser**: For people who need sunlight to function.
- **Urban Professional**: Walkability uber alles.
- **Deal Hunter**: Watches for price drops like a hawk.

## How It Works

1. **Ingestion**: Scrapes Zillow via ZenRows every 6 hours.
2. **Enrichment**: NLP, geospatial, and visual scoring per listing.
3. **Matching**: Weighted scoring against your preferences with soft and hard caps.
4. **Ranking**: Top matches, with explanations of why.

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
├── frontend/               # Vite + React app
├── scripts/                # Data tools
├── run_local.sh            # Start API
├── run_frontend.sh         # Start frontend
└── nuke_db.sh              # Reset database
```

## API Endpoints

| Endpoint | What it does |
|----------|--------------|
| `GET /matches/test-user` | Your ranked matches |
| `GET /listings` | All listings, paginated |
| `GET /listings/{id}` | Single listing |
| `GET /listings/{id}/history` | Change history for a listing |
| `GET /changes` | Recent listing changes |
| `POST /admin/ingestion/run` | Force a data refresh |
| `GET /ingestion/status` | Ingestion status |
| `GET /ping` | Health check |

## Development

Burn it down and start over:

```bash
./nuke_db.sh && ./run_local.sh
python scripts/import_from_json.py
```

Run visual analysis:

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

Optional alerts (iMessage / email / SMS) are documented in `docs/DEVELOPMENT.md`.

## Stack

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Frontend**: Vite, React 18, TypeScript, React Query
- **Database**: SQLite local, PostgreSQL in Docker
- **AI**: Claude Vision

MIT licensed. Do whatever.
