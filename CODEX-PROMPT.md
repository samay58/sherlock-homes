# Codex Session: Sherlock Homes 10x Implementation

## Context

You're working on **Sherlock Homes**, an SF real estate intelligence platform. The goal: surface the 2-3 listings worth jumping on, not drown in inventory like everyone else on Zillow.

**Read these files first (in order):**
1. `CLAUDE.md` — Project overview, architecture, commands
2. `docs/10X_SPEC.md` — Product vision and capability map
3. `docs/BUYER-CRITERIA-HANDOFF.md` — **CRITICAL** — Comprehensive buyer criteria from deep Q&A session (16K of actionable intelligence)
4. `config/user_criteria.yaml` — Machine-readable criteria config

---

## Your Mission

### Phase 1: Deep Code Review

Before writing anything, thoroughly audit the existing codebase:

```
app/
├── services/       # Core logic lives here
├── models/         # SQLAlchemy models
├── routes/         # FastAPI endpoints
├── providers/      # Data ingestion (Zillow via ZenRows)
├── schemas/        # Pydantic schemas
└── scripts/        # Utility scripts
```

**For each file, assess:**
- Does it exist and work, or is it spec/placeholder?
- Is it aligned with the 10X_SPEC vision?
- Is the code clean, or does it need refactoring?
- What's missing vs. what BUYER-CRITERIA-HANDOFF.md requires?

**Produce a gap analysis**: What exists vs. what's needed for the full scoring engine.

---

### Phase 2: Implement the Scoring Engine

The heart of Sherlock Homes is the **PropertyMatcher**. Using `BUYER-CRITERIA-HANDOFF.md` as the spec:

#### 2.1 Hard Filters (Binary Pass/Fail)
```python
# Must implement these as pre-filter before scoring
HARD_FILTERS = {
    "price_max": 3_500_000,
    "bedrooms_min": 3,
    "bathrooms_min": 2,
    "sqft_min": 1600,
    "neighborhoods": [...],  # See handoff doc
}
```

#### 2.2 Weighted Scoring (126-point scale)
Implement the 17 criteria with exact weights from the handoff:
- Tier 1 (57 pts): natural_light, outdoor_space, character_soul, kitchen_quality, location_quiet
- Tier 2 (38 pts): office_space, indoor_outdoor_flow, high_ceilings, layout_intelligence, move_in_ready, views
- Tier 3 (26 pts): in_unit_laundry, parking, central_hvac, gas_stove, dishwasher, storage

#### 2.3 NLP Keyword Extraction
Build `services/nlp.py` with:
- Positive signal detection (light, character, outdoor, kitchen, quality keywords)
- Negative signal detection (flipper, dark, condition, noise keywords)
- Weighted scoring multipliers (1.5x for light, 0.6x for dark signals, etc.)
- Context-aware logic: "cozy" is negative UNLESS combined with light keywords

#### 2.4 Location Intelligence
Build `services/geospatial.py` with:
- Street-level boost/penalize lists
- Neighborhood micro-targeting
- Tranquility score calculation
- Penalty conditions (first_floor_busy_street, adjacent_to_bar, etc.)

#### 2.5 Visual Scoring (Claude Vision)
Build `services/visual_scoring.py` with:
- Photo analysis prompts from handoff doc
- Positive/negative visual signal detection
- Light quality assessment
- Flipper detection (gray palette, LVP flooring, staged furniture)

---

### Phase 3: Explainability & Alerts

#### 3.1 Explainability Payload
Every match must include:
```json
{
    "score": 94,
    "score_percent": "75%",
    "tier": "Strong",
    "top_positives": ["...", "...", "..."],
    "key_tradeoff": "...",
    "signals": {
        "tranquility_score": 8.2,
        "light_potential": 9.1,
        "visual_quality": 7.8,
        "nlp_character_score": 8.5
    },
    "why_now": "Price dropped 6% yesterday after 52 DOM"
}
```

#### 3.2 Alert System
Implement thresholds from handoff:
- Immediate: new listing 76+, price drop 5%+, back on market
- Digest: DOM > 45 days, small price drops

---

### Phase 4: Streamline & Elegance

**Design principles:**
- **Opinionated defaults**: The criteria are already defined. Don't build a generic "configure anything" system. Build for THIS buyer.
- **Minimal UI**: The value is in the scoring, not fancy dashboards. A clean list of ranked matches with explainability.
- **Fast feedback loop**: From ingestion to scored match should be fast. Optimize the pipeline.
- **Trustworthy**: Show work. No black box scores. Always explain why.

**Code quality:**
- Clean service-layer pattern (already started)
- Type hints everywhere
- Docstrings for complex logic
- Tests for scoring edge cases

---

## Technical Constraints

- Python 3.11 or 3.12 (spaCy compatibility)
- FastAPI backend, SvelteKit frontend
- SQLite for dev, PostgreSQL for prod
- Claude API for vision scoring (ANTHROPIC_API_KEY)
- ZenRows for Zillow data (ZENROWS_API_KEY)

---

## Success Criteria

When done, I should be able to:

1. **Run ingestion**: `POST /admin/ingestion/run` pulls SF listings
2. **Get ranked matches**: `GET /matches/test-user` returns scored listings with full explainability
3. **See why**: Each match shows top 3 positives, key tradeoff, and signal breakdown
4. **Get alerts**: Price drops and new high-score listings trigger immediate notification
5. **Trust it**: Scores align with the criteria in BUYER-CRITERIA-HANDOFF.md

---

## What NOT To Do

- Don't build a generic multi-user system. This is for one buyer (Samay & Kamya).
- Don't over-engineer the UI. Functionality over polish.
- Don't add features not in the spec. Scope is defined.
- Don't ignore the soft caps and penalties. They matter.
- Don't make scores opaque. Explainability is core.

---

## Getting Started

```bash
# Start here
cat CLAUDE.md
cat docs/10X_SPEC.md
cat docs/BUYER-CRITERIA-HANDOFF.md

# Then audit
find app -name "*.py" -exec wc -l {} \;
ls -la app/services/

# Then implement
# Start with PropertyMatcher scoring, then NLP, then geospatial, then visual
```

---

*When you've read the three key docs and audited the code, give me a gap analysis and implementation plan before writing code.*
