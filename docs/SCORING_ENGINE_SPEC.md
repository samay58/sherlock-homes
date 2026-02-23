# Sherlock Homes — Buyer Scoring Engine Spec (Samay & Kamya) v1

**Status:** Draft (ready to implement)  
**Last Updated:** 2026-01-19  
**Source of truth:** `config/user_criteria.yaml` (derived from `docs/BUYER-CRITERIA-HANDOFF.md`)

## Objective

Surface the **2–3 listings worth immediate action** by applying an opinionated, buyer-specific scoring engine:

1) **Hard filters** (binary pass/fail)  
2) **126-point weighted scorecard** (17 criteria, 0–10 each)  
3) **Explainability** (top positives + key tradeoff + “why now”)  
4) **Alerts** (immediate vs digest)  

This system is **not** a generic “configure anything” matcher. It is built for **Samay & Kamya**.

## Implementation Status (Current)

- Backend scoring engine, alerts, OpenAI vision scoring, and text intelligence are implemented.
- Matches endpoint returns explainability fields (top positives, tradeoff, why-now, signals).
- Visual scoring script supports targeting top matches: `python -m app.scripts.analyze_visual_scores --top-matches N`.
- Cost logging is optional (set OpenAI cost env vars to estimate spend).
- Frontend matches cards show explainability and signals; browse cards now show updated intel tags.
- Frontend local dev uses SSR API base defaulting to `http://localhost:8000` (override with `VITE_API_TARGET`).
- Listing detail view now surfaces explainability, signals, and match narrative (on-demand scoring).

## Inputs

### Listing data (DB: `PropertyListing`)
- Address, neighborhood, price, beds, baths, sqft, type, description, photos, days_on_market, status
- Parsed/derived flags (keywords, red flags, deal signals)
- Cached intelligence (tranquility, light potential, visual score, etc.)
- Source tracking: `source`, `source_listing_id`, `sources_seen`, `last_seen_at`

### Change events (DB: `ListingEvent`)
- price_drop, price_increase, status_change, back_on_market, photo_change, description_change, new_listing

### Buyer config (YAML: `config/user_criteria.yaml`)
- `hard_filters`, `soft_caps`, `weights`, `nlp_signals`, `location_modifiers`, `alerts`, `visual_preferences`, `explain`

## Non-goals
- Multi-user personalization (beyond the single buyer profile)
- A generic UI/dashboard (minimal ranked list + explanations only)
- Allowing opaque model-only scoring without evidence (trust requires “show work”)

---

## Scoring Pipeline (Ordered)

### 0) Normalize + prepare
- Normalize neighborhood names and infer neighborhood from lat/lon when missing.
- Normalize prices, status, and compute stable hashes for text/photos for caching.

### 1) Hard Filters (binary pre-filter)
Fail any => **do not score or surface**.

From YAML `hard_filters`:
- `price_max`
- `bedrooms_min`
- `bathrooms_min`
- `sqft_min`
- `neighborhoods` allowlist

Additional binary checks (from handoff):
- **Not dark** (must plausibly be bright on cloudy day)
- **Quiet street** (no traffic roar, no bar noise)
- **Layout flows**
- **Guest parking feasible** (street parking exists)
- **1 bath has tub**

Implementation note: some checks may be **Unknown** from data; treat as:
- v1: don’t hard-fail unless confidently known false; instead surface as “unknown” and potentially a tradeoff.

### 2) Criterion Scores (17 × 0–10)
For each criterion, compute a score `0..10` plus:
- `confidence` (high/medium/low)
- `evidence` (strings/quotes/signals)

Then compute weighted total on a 126-point scale:

```
total = round(sum((criterion_score / 10) * weight for criterion, weight in WEIGHTS.items()))
```

Weights (source: YAML `weights`):
- Tier 1 (57): `natural_light` 15, `outdoor_space` 12, `character_soul` 10, `kitchen_quality` 10, `location_quiet` 10
- Tier 2 (38): `office_space` 8, `indoor_outdoor_flow` 8, `high_ceilings` 6, `layout_intelligence` 6, `move_in_ready` 5, `views` 5
- Tier 3 (26): `in_unit_laundry` 6, `parking` 6, `central_hvac` 4, `gas_stove` 4, `dishwasher` 3, `storage` 3

### 3) Soft Caps (penalty above, not disqualification)
From YAML `soft_caps`:
- `price_soft` (ideal ceiling)
- `hoa_soft`

Penalty rules (handoff):
- Price above `price_soft`: apply a graded penalty that increases up to the hard cap.
- HOA:
  - `< $400`: yellow flag (“deferred maintenance risk”), no score penalty by default
  - `$400–$800`: neutral
  - `$800–$1,000`: -5 points (needs justification)
  - `> $1,000`: -10 points (needs strong amenities)

### 4) Intelligence layers (inputs to criterion scoring)

#### 4.1 Keyword NLP (fast, deterministic)
Driven by YAML `nlp_signals`:
- Positive groups with multipliers: light (1.5x), character (1.3x), outdoor (1.4x), kitchen (1.2x), quality (1.3x)
- Negative groups with multipliers: flipper (0.7x), dark (0.6x), condition (0.5x), location_noise (0.7x), weak_outdoor (0.8x)

Context rules (handoff):
- “cozy/intimate/charming” is **negative only if** *no light positives* are present.
- “move-in ready” is **only a flipper signal** if paired with generic/low-information description.

Outputs:
- Per-criterion partial scores and evidence (matched keywords).
- Dedicated `nlp_character_score` signal for explainability.

#### 4.2 Geospatial / location intelligence (deterministic + heuristic)
Inputs:
- Tranquility score (0–100)
- Street-level modifiers (YAML `location_modifiers`):
  - `boost_streets`
  - `penalize_streets`
  - `penalize_conditions` (e.g., `adjacent_to_bar`, `on_major_thoroughfare`)

Outputs:
- `location_quiet` criterion score + evidence
- `tranquility_score` signal in explainability

#### 4.3 Visual scoring (OpenAI Vision)
Goal: detect light quality, character markers, flipper tells, deferred maintenance.

Inputs:
- A sample of photos (configurable)
- Visual prompt aligned to YAML `visual_preferences` and handoff lists

Outputs:
- `visual_quality` signal (0–10 or 0–100 mapped)
- Evidence: highlights + red flags (e.g., gray/LVP, staging, all lights on)
- Feeds into criteria like `natural_light`, `character_soul`, `move_in_ready`, `kitchen_quality`

Provider (v1):
- Use **OpenAI** for photo analysis (Responses API with image inputs).

#### 4.4 Text LLM Intelligence (supplemental, explainability-first)
This is a supplemental layer used to improve explainability fields. It is not the primary source of the match score.

Guardrails:
- JSON-only output
- Evidence must be verbatim quotes from the input payload
- If evidence is missing, return null/[] (no guessing)

When it runs (current implementation):
- After base scoring, for the top `OPENAI_TEXT_MAX_LISTINGS` listings (default 5)
- Only when `include_intelligence=true` for the request (matches endpoints default to true)
- Cached in-process by payload hash (no TTL; cache resets on process restart)

Inputs (constructed per listing):
- Key facts (beds/baths/sqft/price/neighborhood/DOM)
- Full description
- Recent timeline derived from `ListingEvent` rows

Outputs (schema, v1):
```json
{
  "criterion_hints": {
    "natural_light": {"score_0_10": 7, "confidence": "medium", "evidence": ["..."]}
  },
  "tradeoff_candidates": ["..."],
  "top_positive_candidates": ["..."],
  "red_flags": ["..."],
  "why_now": "..."
}
```

Integration (v1):
- Results are used to update explainability fields (`top_positives`, `key_tradeoff`, `why_now`).
- Scores/weights are still computed deterministically from DB columns + deterministic intelligence (NLP/geospatial/vision).

Providers:
- OpenAI first (when `OPENAI_API_KEY` is set)
- DeepInfra fallback (OpenAI-compatible API) when OpenAI fails or is unset and `DEEPINFRA_API_KEY` is set

Key settings:
- `OPENAI_TEXT_MAX_LISTINGS` (0 disables)
- `OPENAI_TEXT_MODEL`, `OPENAI_TEXT_MODEL_HARD`
- `DEEPINFRA_TEXT_MODEL`, `DEEPINFRA_TEXT_MODEL_HARD`, `DEEPINFRA_BASE_URL`

---

## Explainability Output (required)

Every returned match includes:
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

Tier mapping (handoff):
- 100+ = Exceptional
- 88–99 = Strong
- 76–87 = Interesting
- <76 = Pass

## Alerts (required)

From YAML `alerts`:
- Immediate:
  - new listing with score ≥ 76
  - price drop ≥ 5%
  - back on market
- Daily digest:
  - DOM ≥ 45 days (negotiation opportunity)
  - small price drops (e.g., 3%)

Alerts must be:
- deduped
- quiet-by-design (digest grouping)
- self-contained (top matches + why now)

---

## Listings Source Expansion (Phase 2)

Goal: widen coverage beyond Zillow while keeping data quality high and duplicates low.

Scope:
- ZenRows-supported sources (prioritize those with structured APIs).
- Curated high-taste realtor sources (e.g., Priya Agarwal) when feasible.

Design:
- Add `source` + `source_listing_id` fields to `PropertyListing` and enforce uniqueness on `(source, source_listing_id)` to prevent collisions.
- Track provenance: `sources_seen` list plus `last_seen_at` per listing.
- Introduce a provider registry that normalizes listing payloads into a single canonical shape:
  - `address`, `price`, `beds`, `baths`, `sqft`, `lat`, `lon`, `url`, `listing_status`, `photos`, `description`, `days_on_market`
  - `source` and `source_listing_id`
- Enrichment supports JSON-LD plus embedded state parsing (`__NEXT_DATA__`, `window.__PRELOADED_STATE__`) to fill beds/baths/sqft when needed.
- Dedupe policy:
  - First pass: `(source, source_listing_id)`
  - Second pass: fuzzy address + geospatial proximity (merge photo sets, prefer richer descriptions)
- Track `last_seen_at` per source and keep a `sources_seen` array for provenance.
- Default ingestion sources: `INGESTION_SOURCES=zillow` (comma-separated list).
- Curated sources file: `CURATED_SOURCES_PATH=config/curated_sources.yaml`.
- For non-Zillow sources, store `listing_id` as `{source}:{source_listing_id}` when short enough; otherwise hash to keep within 64 chars.
- `source_listing_id` may be a canonical URL for sites without stable numeric IDs (expanded column length).

ZenRows sources (status):
- Zillow (implemented via ZenRows real estate APIs)
- Trulia (implemented via ZenRows universal)
- Realtor.com (implemented via ZenRows universal)
- Craigslist (implemented via ZenRows universal; best-effort parsing)
- Redfin (direct API adapter with ZenRows fallback + HTML/embedded JSON parsing)

Curated realtor sources:
- Curated provider reads `config/curated_sources.yaml` (manual listings + optional URLs).
- If a realtor site is available and stable, use ZenRows + HTML parser for enrichment.
- If not, support manual CSV import into the same normalized shape.
- Treat these sources as high-signal but low-volume; prioritize freshness.

Operational constraints:
- Rate limit per source; honor ZenRows quotas.
- Ingestion toggles per source (config flags).
- Fail-soft: one provider failure should not block others.

Outputs:
- Unified listings pipeline feeding the same scoring engine.
- Source attribution in explainability payload (for trust).

---

## Acceptance Criteria (checklist)
- Ingestion produces listings with normalized neighborhood and persisted snapshots/events.
- `/matches/test-user` returns ranked matches using hard filters + 126-point scoring.
- Each match includes structured explainability payload (top 3 positives, 1 tradeoff, signals, why_now).
- Alerts fire for the configured triggers (immediate + digest), using existing delivery channels.
- Text LLM intelligence is optional, cached, evidence-based, and does not make opaque claims.
