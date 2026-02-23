# Sherlock Homes: Session Progress Log

> Archived: historical session notes. Treat as context/history, not as the current runbook.

**Last Updated**: January 19, 2026 (Session 12)

---

## WHERE WE LEFT OFF

### Completed This Session
- **sherlock-6rh** CLOSED: Bounded weight learning system
  - 4 API endpoints: GET/DELETE `/users/{id}/weights`, GET `/weights/summary`, POST `/weights/recalculate`
  - Learning from like/dislike feedback with bounded deltas
  - Integrated with PropertyMatcher for personalized scoring

### Phase Status
| Phase | Status | Key Deliverable |
|-------|--------|-----------------|
| Phase 1: Scoring Engine | **COMPLETE** | 17-criteria weighted scoring, visual + tranquility intelligence |
| Phase 2: Personalization | **90% COMPLETE** | Feedback capture + weight learning done. Compare view remaining. |
| Phase 3: Location Intelligence | NOT STARTED | Map filters, neighborhood deep-dives |

### Next Session: Pick One
1. **sherlock-b0c** [P2] - Compare view (side-by-side 2-4 listings)
2. **sherlock-7li** [P2] - Map polygon/neighborhood filters
3. **sherlock-1rc** - Close Phase 2 epic if compare view done

### Beads Summary
```
Open: 18 | Closed: 30 | Blocked: 4 | Ready: 14
```

### Quick Start
```bash
cd ~/home-hog
bd ready                    # See available work
bd show sherlock-b0c        # Review next task
./run_local.sh              # Start API
./run_frontend.sh           # Start frontend
```

---

## Current System State

| Component | Status | Notes |
|-----------|--------|-------|
| Database | SQLite | `DATABASE_URL` is local SQLite (currently `homehog.db`) |
| API | Running | `./run_local.sh` → http://localhost:8000 |
| Frontend | SvelteKit | `./run_frontend.sh` → http://localhost:5173 |
| Visual Scoring | **Active** | OpenAI Vision (`OPENAI_API_KEY`); set `OPENAI_VISION_COST_PER_IMAGE_USD` for cost logs |
| Docker | Available | Fallback via `.env.docker` |
| Alerts | **Available** | iMessage (macOS relay), email (SMTP), SMS fallback, webhook |

### Quick Runbook (Local)
1. Activate env: `source .venv/bin/activate`
2. Reset DB: `./nuke_db.sh`
3. Migrate: `alembic upgrade head`
4. Ingest all sources:
   - `INGESTION_SOURCES=zillow,redfin,trulia,realtor,craigslist,curated python -c "from app.services.ingestion import run_ingestion_job_sync; run_ingestion_job_sync()"`
5. Count listings: `sqlite3 homehog.db "select count(*) from property_listings;"`
6. Visual scoring dry run: `python -m app.scripts.analyze_visual_scores --dry-run`
7. Visual scoring full run: `python -m app.scripts.analyze_visual_scores`
8. Tests: `PYTHONPATH=. pytest -q`

### Known Runtime Notes (Jan 2026)
- Redfin ZenRows search can return 422; fallback now retries without premium proxy.
- Trulia detail pages can return 410; incomplete URLs are now skipped as non-fatal.
- If ingestion fails on DNS, verify `api.zenrows.com` resolves (`curl -I https://api.zenrows.com` should return 405).

### Visual Scoring Stats (Session 4 snapshot)
- These numbers were captured during Session 4 and will vary with current data.
- **Coverage**: 100% (41/41 listings)
- **Average Score**: 82.3/100
- **Score Range**: 39-94
- **Cost**: $0.32 total (~$0.008/listing)

---

## Session History

### Session 12: January 19, 2026 - Bounded Weight Learning System

**Objective**: Implement personalized scoring via bounded weight learning from user feedback.

**Completed**:
- [x] Created migration for `learned_weights` JSON column on users table
- [x] Implemented weight learning service with bounded deltas
- [x] Added four API endpoints for weight management
- [x] Integrated learned weights with PropertyMatcher scoring
- [x] **Closed sherlock-6rh** - bounded weight learning complete

**Learning Algorithm**:
| Parameter | Value |
|-----------|-------|
| Delta per signal | ±0.05 |
| Max delta per recalc | ±0.5 |
| Min signals required | 5 total (3 likes, 2 dislikes) |
| Multiplier bounds | [0.5x, 2.0x] of base weight |

**API Endpoints**:
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/users/{id}/weights` | GET | View base, learned, and effective weights |
| `/users/{id}/weights/summary` | GET | Human-readable preference insights |
| `/users/{id}/weights/recalculate` | POST | Trigger learning from feedback |
| `/users/{id}/weights` | DELETE | Reset to default weights |

**Files Created/Modified**:
| File | Purpose |
|------|---------|
| `app/services/weight_learning.py` | Learning algorithm with bounded deltas |
| `app/routes/users.py` | Weight management endpoints |
| `app/schemas/user.py` | Weight-related Pydantic schemas |
| `app/models/user.py` | Added `learned_weights` JSON column |
| `app/services/advanced_matching.py` | PropertyMatcher accepts user_weights |
| `app/routes/listings.py` | Matches endpoint uses learned weights |
| `migrations/versions/20260119_add_learned_weights.py` | DB migration |

**How It Works**:
1. User likes/dislikes listings → feedback stored in DB
2. `POST /users/{id}/weights/recalculate` analyzes feedback
3. For liked listings: top 3 scoring criteria get boosted
4. For disliked listings: top 3 scoring criteria get reduced
5. Deltas are bounded to prevent overfitting
6. `GET /matches/user/{id}` now uses learned weights for scoring

---

### Session 11: January 19, 2026 - Phase 1 Validation + Feedback Capture

**Objective**: Validate Session 10 pipeline and implement feedback capture for weight learning.

**Completed**:
- [x] Validated full ingestion pipeline (41 Zillow listings)
- [x] Confirmed 100% visual scoring coverage
- [x] Confirmed 100% tranquility scoring coverage
- [x] Validated scoring engine (17 criteria, correct tier classification)
- [x] Verified match explainability (top_positives, key_tradeoff, why_now)
- [x] **Closed Phase 1 Epic (sherlock-knh)** - buyer scoring engine complete
- [x] **Feedback capture (sherlock-ms9)** - like/dislike/neutral buttons, API, DB persistence

**Validation Results**:
| Metric | Value |
|--------|-------|
| Listings | 41 (Zillow) |
| Visual Scored | 100% |
| Tranquility Scored | 100% |
| Score Range | 34-54% (all Pass tier) |
| Feature Scores | All 17 criteria populated |

**Files Updated**:
| File | Purpose |
|------|---------|
| `app/models/feedback.py` | ListingFeedback model |
| `app/routes/feedback.py` | Feedback API endpoints |
| `app/schemas/feedback.py` | Feedback Pydantic schemas |
| `migrations/versions/YYYYMMDD_add_feedback.py` | Feedback table migration |
| `frontend/src/lib/components/DossierCard.svelte` | Feedback buttons UI |
| `frontend/src/lib/api.ts` | Feedback API calls |

### Session 10: January 19, 2026 - Multi-Source Ingestion + OpenAI Vision

**Objective**: Expand ingestion sources, stabilize local SQLite, and switch visual scoring to OpenAI.

**Completed**:
- [x] Added multi-source ingestion (Redfin, Trulia, Realtor, Craigslist, curated sources)
- [x] Implemented HTML parsing via JSON-LD and embedded state
- [x] Added source tracking + hashed listing ids for multi-provider dedupe
- [x] Switched visual scoring to OpenAI Vision (Claude deprecated for now)
- [x] Fixed SQLite primary key issue blocking listing events
- [x] Hardened ZenRows timeouts + retry/backoff
- [x] Stabilized Redfin fallback and Trulia detail failures as non-fatal

**Files Updated**:
| File | Purpose |
|------|---------|
| `app/providers/` | New providers + HTML parsing + ZenRows client |
| `app/services/ingestion.py` | Source normalization + enrichment flow |
| `app/services/persistence.py` | Source-based IDs + event creation |
| `app/services/visual_scoring.py` | OpenAI Vision integration |
| `app/core/config.py` | ZenRows timeout + OpenAI config |
| `migrations/versions/2eaa91ec76da_init_tables.py` | SQLite PK fix |
| `docs/SCORING_ENGINE_SPEC.md` | Multi-source + intelligence spec |
| `tests/test_html_parsing.py` | Parsing coverage |

**Next Steps**:
- Run full ingestion and confirm listing coverage per source.
- Run visual scoring to validate cost + end-to-end match explainability.
- Validate `/matches/test-user` output (top 3 positives, tradeoffs, signals).

### Session 9: December 20, 2025 - Docs Polish + Local Install Reliability

**Objective**: Keep docs fresh and make local installs resilient to dependency changes.

**Completed**:
- [x] Rewrote README with updated voice and current features
- [x] Added end-to-end smoke test steps to Development guide
- [x] Made `run_local.sh` re-install when `requirements.txt` changes
- [x] Documented focus shift in 10x spec

**Files Updated**:
| File | Purpose |
|------|---------|
| `README.md` | Updated product overview |
| `docs/DEVELOPMENT.md` | Smoke test steps + install behavior |
| `run_local.sh` | Requirements hash check |
| `docs/10X_SPEC.md` | Focus note |

### Session 5: December 20, 2025 - 10x Spec + Alert Delivery

**Objective**: Define the 10x roadmap and implement real alert delivery (iMessage/email/SMS/webhook).

**Completed**:
- [x] Authored comprehensive 10x product spec
- [x] Added alert delivery service (iMessage, SMTP email, Twilio SMS, webhook)
- [x] Integrated scout alerts with real delivery channels
- [x] Added alert configuration settings

**Files Updated**:
| File | Purpose |
|------|---------|
| `docs/10X_SPEC.md` | 10x roadmap and spec |
| `app/services/alerts.py` | Alert delivery (iMessage/email/SMS/webhook) |
| `app/services/scout.py` | Uses real alert delivery |
| `app/core/config.py` | Alert config settings |

### Session 6: December 20, 2025 - Listing Change Tracking

**Objective**: Add listing snapshots + events with history endpoints.

**Completed**:
- [x] Snapshot + event models for listing changes
- [x] Event creation during ingestion upserts
- [x] Listing history and change feed endpoints
- [x] Alembic migration for new tables

**Files Updated**:
| File | Purpose |
|------|---------|
| `app/models/listing_event.py` | Snapshot + event models |
| `app/services/persistence.py` | Create snapshots + events |
| `app/routes/listings.py` | History + change feed endpoints |
| `app/schemas/listing_event.py` | API schemas for events |
| `migrations/versions/20251220_add_listing_events.py` | Alembic migration |

### Session 7: December 20, 2025 - Matching Quality Tuning

**Objective**: Reduce noise by enforcing budget caps, neighborhood focus, and recency-aware scoring.

**Completed**:
- [x] Added neighborhood normalization + SF focus mapping
- [x] Added soft budget cap + recency weighting in scoring
- [x] Enforced strict neighborhood filtering mode
- [x] Added minimal, focused criteria UI for budget/neighborhood/recency
- [x] Added criteria fields + migration for matching quality tuning

**Files Updated**:
| File | Purpose |
|------|---------|
| `app/services/neighborhoods.py` | Neighborhood normalization and mapping |
| `app/services/ingestion.py` | Neighborhood normalization on ingest |
| `app/services/persistence.py` | Neighborhood fallback |
| `app/models/criteria.py` | Soft cap + neighborhood/recency fields |
| `app/services/advanced_matching.py` | Budget + recency scoring, strict neighborhoods |
| `app/services/vibe_presets.py` | Added default weights |
| `app/schemas/criteria.py` | New criteria fields |
| `frontend/src/routes/criteria/+page.svelte` | Minimal criteria UI |
| `frontend/src/lib/types.ts` | Updated types |
| `migrations/versions/20251220_add_matching_quality_fields.py` | Alembic migration |

### Session 8: December 20, 2025 - Why This Matched + Stability Fixes

**Objective**: Add explicit match explanations and fix local dev errors.

**Completed**:
- [x] Added match reasons + tradeoff explanations to matching output
- [x] Rendered “Why this matched” in match cards
- [x] Fixed ingestion status timezone error
- [x] Pinned bcrypt to fix passlib startup error
- [x] Refreshed README and API documentation

**Files Updated**:
| File | Purpose |
|------|---------|
| `app/services/advanced_matching.py` | Match explanations + recency reasoning |
| `app/schemas/property.py` | Match reason fields in API |
| `frontend/src/lib/components/DossierCard.svelte` | “Why this matched” UI |
| `requirements.txt` | bcrypt pin |
| `app/routes/listings.py` | Ingestion status fix |
| `README.md` | Updated product doc |
| `docs/API.md` | Updated API doc |
| `docs/DEVELOPMENT.md` | Troubleshooting |

### Session 4: December 6, 2025 - Visual Scoring Activation

**Objective**: Enable and test Claude Vision photo analysis

**Completed**:
- [x] Added ANTHROPIC_API_KEY to `.env.local`
- [x] Installed anthropic SDK
- [x] Ran dry-run verification (41 listings ready)
- [x] Limited test (5 listings) - all succeeded
- [x] Full analysis on all 41 listings - 100% success
- [x] Verified integration with matching algorithm
- [x] End-to-end testing of `/matches/test-user` endpoint

**Results**:
| Metric | Value |
|--------|-------|
| Listings analyzed | 41/41 (100%) |
| Success rate | 100% |
| Average score | 82.3/100 |
| Score range | 39 - 94 |
| Cost | $0.32 |

**Score Distribution**:
- Stunning (85+): 16 listings
- Very Appealing (70-84): 23 listings
- Average (50-69): 1 listing
- Needs Work (<50): 1 listing

**Top Matches (with visual integration)**:
| Rank | Match | Visual | Price | Address |
|------|-------|--------|-------|---------|
| 1 | 80.2 | 93 | $1.85M | 1319 Lyon St |
| 2 | 78.2 | 92 | $1.93M | 2678 Sacramento St |
| 3 | 67.6 | 86 | $2.50M | 11 Sherwood Ct |

---

### Session 3: December 6, 2025 - "Lite Route" Migration

**Objective**: Migrate from Docker/PostgreSQL to SQLite for rapid local development

**Completed**:
- [x] Exported 41 listings from PostgreSQL
- [x] Created SQLite-compatible database layer
- [x] Auto-create tables on startup (replaces Alembic for local dev)
- [x] Cross-database query compatibility (`.ilike()` → `.like()`)
- [x] Local development scripts

**Files Created**:
| File | Purpose |
|------|---------|
| `scripts/export_to_json.py` | Export PostgreSQL → JSON |
| `scripts/import_from_json.py` | Import JSON → SQLite |
| `run_local.sh` | Start API locally |
| `run_frontend.sh` | Start frontend locally |
| `nuke_db.sh` | Reset database |

**Impact**:
- Startup: 30s → 1s (30x faster)
- Schema changes: 5min → 45sec (7x faster)
- No Docker required for development

---

### Session 2: December 5, 2025 - Visual Scoring Implementation

**Objective**: Build Claude Vision photo analysis infrastructure

**Completed**:
- [x] Database schema for visual scoring columns
- [x] Visual scoring service with Claude Vision API
- [x] Batch analysis script with caching
- [x] Integration with advanced matching algorithm
- [x] Vibe presets updated with visual_quality weight (8)

**Files Created**:
| File | Purpose |
|------|---------|
| `app/services/visual_scoring.py` | Claude Vision integration |
| `app/scripts/analyze_visual_scores.py` | Batch photo analysis |

---

### Session 1: November 17, 2025 - Foundation & Intelligent Scoring

**Objective**: Project setup, ZenRows configuration, scoring system fix

**Completed**:
- [x] ZenRows API configuration (paid plan)
- [x] Keyword expansion (3x per category: 17→32+ natural light, etc.)
- [x] Multi-factor scoring system working
- [x] Test user initialization

---

## Development Workflow

### Daily Development
```bash
# Terminal 1: Start API
./run_local.sh

# Terminal 2: Start frontend
./run_frontend.sh
```

### Schema Changes
```bash
./nuke_db.sh && ./run_local.sh
python scripts/import_from_json.py  # Re-import data
```

### Visual Scoring
```bash
python -m app.scripts.analyze_visual_scores           # Analyze new listings
python -m app.scripts.analyze_visual_scores --dry-run # Preview only
python -m app.scripts.analyze_visual_scores --all     # Force re-analyze all
```

---

## Key Learnings

### Architecture
1. **Dual-layer scoring**: Ingestion-time NLP flags + query-time weighted scoring
2. **Visual integration**: Claude Vision score (weight 8) adds to multi-factor ranking
3. **Caching**: SHA256 hash of photo URLs prevents redundant API calls

### Cross-Database Compatibility
- SQLite: `check_same_thread=False`, `PRAGMA foreign_keys=ON`
- Queries: Use `.like()` not `.ilike()` for SQLite

### Visual Scoring Economics
- Cost: ~$0.003/image × 3 images/listing = ~$0.008/listing
- 41 listings = $0.32 total
- Cached via `photos_hash` - only re-analyzes when photos change

---

## API Reference

### Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /matches/test-user` | Ranked matches with visual scores |
| `GET /listings` | All listings |
| `GET /listings/{id}` | Single listing |
| `POST /admin/ingestion/run` | Trigger data refresh |
| `GET /ping` | Health check |

### Health Check
```bash
curl http://localhost:8000/ping
curl http://localhost:8000/matches/test-user | jq '.[0]'
```

---

## Configuration

### .env.local
```env
DATABASE_URL=sqlite:///./sherlock.db
RUN_DB_MIGRATIONS_ON_STARTUP=false
ZENROWS_API_KEY=<configured>
ANTHROPIC_API_KEY=<configured>
```

### Feature Weights
```python
{
  "natural_light": 10,
  "view": 9,
  "visual_quality": 8,  # Claude Vision
  "outdoor_space": 8,
  "updated_systems": 7,
  "high_ceilings": 7,
  ...
}
```

---

## Roadmap

### Completed
- [x] NLP keyword extraction (32+ keywords/category)
- [x] Multi-factor scoring algorithm
- [x] SQLite local development
- [x] Claude Vision photo analysis
- [x] Visual scoring integration

### Next Phase: Fresh Data
1. Run new ingestion to get current SF listings
2. Visual score new listings automatically
3. Test full pipeline with fresh data

### Future Enhancements
- Parallel ingestion (asyncio.gather)
- Price tracking & alerts
- Email notifications for high-scoring matches
- Multi-market expansion

---

## File Structure

```
sherlock-homes/
├── run_local.sh              # Start API (SQLite)
├── run_frontend.sh           # Start frontend
├── nuke_db.sh                # Reset database
├── .env.local                # Local config (with API keys)
├── sherlock.db               # SQLite database
├── scripts/
│   ├── export_to_json.py     # PostgreSQL → JSON
│   └── import_from_json.py   # JSON → SQLite
├── app/
│   ├── services/
│   │   ├── visual_scoring.py      # Claude Vision
│   │   ├── advanced_matching.py   # Scoring engine
│   │   └── nlp.py                 # Keyword extraction
│   └── scripts/
│       └── analyze_visual_scores.py
└── frontend/                 # SvelteKit app
```

---

**Status**: Fully operational. Visual scoring active. Ready for fresh data ingestion.
