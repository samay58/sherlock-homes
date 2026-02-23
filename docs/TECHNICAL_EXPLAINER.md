# Sherlock Homes: Full Technical Explainer for External Assessment

> Note (February 22, 2026): This is a historical deep-dive prepared for an external assessment.
> Some details are stale. Key changes since this was written: StreetEasy provider is now implemented,
> Clinton Hill was dropped from the neighborhood list (commute constraint), MAX_DETAIL_CALLS is now 300,
> and the search uses 15 neighborhoods (not 16). For the current codebase map and runbook, start with
> `docs/ARCHITECTURE.md` and `docs/DEVELOPMENT.md`.

## Purpose of This Document

This document provides a comprehensive technical walkthrough of **Sherlock Homes** (codebase: `home-hog`), a property intelligence platform that scrapes real estate listings, enriches them with NLP and computer vision analysis, scores them against weighted buyer criteria, and delivers personalized match alerts. The system was originally built for SF home purchases and has been adapted for NYC rental search.

The goal is to enable an impartial technical reviewer to understand every layer, identify architectural gaps, and propose concrete improvements to make the system 10x more effective at surfacing the best possible rental listings.

---

## 1. System Architecture Overview

```
                        +-----------------+
                        |  .env.local     |
                        |  (API keys,     |
                        |   search config)|
                        +--------+--------+
                                 |
                        +--------v--------+
                        | app/core/       |
                        | config.py       |
                        | (Pydantic       |
                        |  Settings)      |
                        +--------+--------+
                                 |
              +------------------+------------------+
              |                                     |
     +--------v--------+                   +--------v--------+
     | providers/       |                   | config/          |
     | registry.py      |                   | nyc_rental_      |
     | zillow.py        |                   | criteria.yaml    |
     | redfin.py        |                   +--------+---------+
     | trulia.py        |                            |
     | realtor.py       |                   +--------v---------+
     | craigslist.py    |                   | services/         |
     | curated.py       |                   | criteria_config.py|
     +--------+---------+                   | (BuyerCriteria    |
              |                             |  dataclass)       |
              |                             +--------+----------+
     +--------v---------+                            |
     | services/         |                            |
     | ingestion.py      |<---------------------------+
     | (orchestrator)    |
     +--------+----------+
              |
              | For each listing:
              v
     +--------+----------+     +------------------+     +-------------------+
     | services/nlp.py   |     | services/         |     | services/          |
     | (keyword extract, |     | geospatial.py     |     | visual_scoring.py  |
     |  light potential)  |     | (tranquility      |     | (OpenAI Vision     |
     +--------+----------+     |  score, SF only)   |     |  photo analysis)   |
              |                +--------+----------+     +--------+----------+
              |                         |                          |
              +------------+------------+--------------------------+
                           |
                  +--------v----------+
                  | services/          |
                  | persistence.py     |
                  | (upsert + dedup +  |
                  |  change tracking)  |
                  +--------+----------+
                           |
                  +--------v----------+
                  | SQLite/PostgreSQL  |
                  | PropertyListing    |
                  | ListingEvent       |
                  | ListingSnapshot    |
                  +--------+----------+
                           |
              +------------+------------+
              |                         |
     +--------v----------+    +--------v----------+
     | services/          |    | services/          |
     | advanced_matching  |    | listing_alerts.py  |
     | .py (PropertyMatcher|    | (event-driven      |
     |  126-point scoring) |    |  alert dispatch)   |
     +--------+----------+    +--------+----------+
              |                         |
     +--------v----------+    +--------v----------+
     | services/          |    | services/          |
     | text_intelligence  |    | alerts.py          |
     | .py (OpenAI text   |    | (iMessage, SMS,    |
     |  analysis)         |    |  email, webhook)   |
     +--------+----------+    +-------------------+
              |
     +--------v----------+
     | services/          |
     | weight_learning.py |
     | (feedback-driven   |
     |  personalization)  |
     +-------------------+
```

**Stack**: Python 3.11/3.12, FastAPI, SQLAlchemy, SQLite (dev) / PostgreSQL (prod), httpx (async HTTP), React 18 + TypeScript + Vite (frontend).

---

## 2. Data Ingestion Pipeline

### 2.1 Provider System (`providers/`)

The system uses a **registry pattern** where each data source implements a `BaseProvider` interface with `search()`, `get_details()`, and `close()` methods. Active providers are configured via `INGESTION_SOURCES` env var (default: `zillow`).

**Currently implemented providers**: Zillow (active), Redfin, Trulia, Realtor, Craigslist, Curated. Only Zillow is currently used for NYC.

### 2.2 Zillow Provider (`providers/zillow.py`)

The Zillow provider uses **ZenRows** (anti-bot scraping service) with two endpoints:

1. **Discovery endpoint** (`realestate.api.zenrows.com/v1/targets/zillow/discovery/`): Takes a Zillow search URL and returns structured JSON with `property_list` and `pagination` data.

2. **Property detail endpoint** (`realestate.api.zenrows.com/v1/targets/zillow/properties/{zpid}`): Returns full property details for a specific Zillow Property ID (ZPID).

**Multi-location search**: The provider supports searching across 16 NYC neighborhoods simultaneously. Each neighborhood maps to a Zillow URL slug (e.g., `williamsburg-brooklyn-new-york-ny`). The `search_all_locations()` method iterates through all slugs, fetching up to 5 pages per neighborhood with 1.5s delays between pages.

**Rental mode**: When `SEARCH_MODE=rent`, the URL builder inserts `/rentals/` into the path and sets appropriate property types (apartment, condo, townhouse).

**URL construction** builds dynamic filter parameters:
```
https://www.zillow.com/{slug}/rentals/{beds}-_beds/{baths}-_baths/{sqft}-_size/{price_min}-{price_max}_price/{page}_p/
```

**Neighborhood tagging**: ZenRows returns generic borough names ("Brooklyn") instead of specific neighborhoods ("Williamsburg"). A `SLUG_TO_NEIGHBORHOOD` dictionary maps 26 search slugs to canonical neighborhood names. During search result parsing, if the API returns a generic borough, the listing is tagged with the canonical name from the slug being searched.

**Current configuration** (from `.env.local`):
- 16 neighborhood slugs searched
- Price range: $5,000-$9,500/month
- Beds: 1+, Baths: 1+, Sqft: 500+
- MAX_PAGES=20, MAX_DETAIL_CALLS=100
- ZenRows timeout: configured in settings

### 2.3 Ingestion Orchestrator (`services/ingestion.py`)

`run_ingestion_job()` executes the full pipeline:

1. **Fetch summaries**: Calls `_fetch_summaries()` which invokes `provider.search_page()`. For multi-location providers, this triggers `search_all_locations()` on the first page call and returns all results at once.

2. **Enrich with details**: `_enrich_summaries()` iterates through summaries, calling `provider.get_details(listing_id)` for each (up to `MAX_DETAIL_CALLS`). This adds descriptions, photos, year_built, lat/lon, and days_on_market.

3. **Neighborhood preservation**: During detail enrichment, the search-tagged neighborhood is saved before updating with detail response data. If the detail response overwrites with a generic borough name, the tagged neighborhood is restored.

4. **NLP extraction**: `extract_flags()` runs keyword matching on the description to set 13+ boolean feature flags on each listing.

5. **Tranquility scoring**: `calculate_tranquility_score()` runs for listings with lat/lon data. **CRITICAL ISSUE**: This module uses hardcoded SF noise source data (Van Ness Ave, Geary Blvd, US-101, etc.) and produces meaningless scores for NYC listings.

6. **Light potential**: `estimate_light_potential()` generates a 0-100 heuristic score based on description keywords, boolean flags, and photo count.

7. **Persistence**: `upsert_listings()` deduplicates by (source, source_listing_id), then by listing_id, then by URL. Maps NLP flags to model boolean columns. Creates `ListingEvent` records for price drops, status changes, photo updates, and description changes.

8. **Alert processing**: `process_listing_alerts()` evaluates new events against buyer criteria and dispatches alerts via iMessage, SMS, email, or webhook.

### 2.4 Known Ingestion Issues

- **Deduplication waste**: The same ZPID can appear across multiple neighborhood searches. Detail API calls are made before deduplication, wasting API credits. Of 380 upserts in the last run, only 334 were unique.
- **Description coverage**: Only 24 of 334 listings had descriptions after enrichment. MAX_DETAIL_CALLS=100 limits enrichment, and many calls hit duplicates.
- **Chelsea missing**: The `chelsea-new-york-ny` slug may not return results, suggesting a Zillow URL format issue for that neighborhood.
- **No StreetEasy**: ZenRows only supports Zillow and Idealista as dedicated real estate targets. StreetEasy (the dominant NYC rental platform) requires a different approach.

---

## 3. NLP Text Analysis (`services/nlp.py`)

### 3.1 Keyword Extraction

The NLP module defines 500+ keywords across 13 positive feature categories and 3 red flag categories:

**Positive categories**: natural_light (60 keywords), high_ceilings (16), outdoor_space (32), parking (16), view (34), updated_systems (16), home_office (15), storage (16), open_floor_plan (13), architectural_details (20), luxury (18), designer (13), tech_ready (16).

**Red flag categories**: busy_street (17 keywords, includes SF-specific streets), foundation_issues (17), hoa_issues (10).

**Additional red flags**: north_facing_only (4), basement_unit (5), tandem_parking (3), street_parking_only (3).

`extract_flags()` returns a dict of boolean flags indicating which feature categories have keyword matches in the listing description.

### 3.2 Buyer-Specific Signal Analysis

`analyze_text_signals()` uses the NLP signal configuration from the buyer criteria YAML, not the hardcoded keyword lists. This allows per-user customization of what keywords matter and their weights.

The YAML configuration defines 7 positive signal groups (light, pet, gym, outdoor, character, kitchen, amenities, quality) and 6 negative groups (gross_highrise, dark, noise, condition, no_pets, railroad) with associated keywords and weight multipliers.

### 3.3 Light Potential Estimation

`estimate_light_potential()` produces a 0-100 score starting at 50 (neutral), adding up to +25 for positive keywords (sun-filled, corner unit, top floor, etc.) and subtracting up to -30 for negative keywords (north-facing, basement, dark, etc.). Additional modifiers:

- +15 for `has_natural_light_keywords` flag
- -25 for `is_north_facing_only`
- -30 for `is_basement_unit`
- +10 for top floor/penthouse
- +8 for corner unit
- +5 for 15+ photos (bright spaces get photographed more)

### 3.4 Gaps in NLP for NYC Rentals

- **No pet_friendly extraction**: The YAML defines pet keywords but `extract_flags()` doesn't have a `pet_friendly` category. The scoring engine has `pet_friendly` in its weights but no column or extraction logic exists.
- **No gym_fitness extraction**: Same issue. Weight defined (10 points) but no extraction pipeline.
- **No building_quality extraction**: Weight defined (6 points) but no extraction.
- **No doorman_concierge extraction**: Weight defined (4 points) but no extraction.
- **SF-specific busy street keywords**: "van ness", "geary", "19th avenue", "market street", "mission street", "columbus", "lombard street" are SF streets in the busy_street detection list, irrelevant for NYC.

---

## 4. Geospatial Intelligence (`services/geospatial.py`)

### 4.1 Tranquility Score

Calculates a 0-100 score based on proximity to noise sources using haversine distance calculations. Higher score = quieter location.

**Penalty structure**:
- Busy streets: -35 (on street) to -8 (2 blocks away), weighted by severity (0.6-0.9)
- Freeways: -40 (adjacent) to -10 (500m away)
- Fire stations: -10 (<150m) to -5 (<300m)

### 4.2 CRITICAL: Entirely SF-Locked

The tranquility module is **completely hardcoded for San Francisco**:
- `SF_BUSY_STREETS`: 10 SF streets (Van Ness, Geary, 19th Ave, Mission, Market, Divisadero, Lombard, Columbus, Folsom, Broadway)
- `SF_FREEWAYS`: 3 SF freeways (US-101, I-280, I-80 Bay Bridge)
- `SF_FIRE_STATIONS`: 8 SF fire stations

For NYC listings, the nearest noise source will always be thousands of kilometers away, producing a score of 100 (perfect tranquility) for every listing. This data is actively misleading.

### 4.3 Location Modifiers

`apply_location_modifiers()` is location-agnostic and uses the YAML config to boost/penalize based on street names in the address. The NYC criteria YAML includes:
- **Boost streets**: Berry St, N 6th St, Kent Ave, Wythe Ave, Montague St, Perry St, Charles St, Bank St, Commerce St, Madison Ave, Park Ave South
- **Penalize streets**: Broadway, Canal St, Houston St, Bowery, Delancey St, FDR Drive, BQE
- **Penalize conditions**: first_floor_busy_street, adjacent_to_bar, on_major_thoroughfare, above_restaurant

This part works correctly for NYC but depends on the address and description text containing these street names.

---

## 5. Visual Scoring (`services/visual_scoring.py`)

### 5.1 OpenAI Vision Analysis

Uses OpenAI's Vision API to analyze property photos across 5 dimensions (0-100 each):
1. **Modernity** (25% weight): finishes, fixtures, design recency
2. **Condition** (25%): maintenance state
3. **Brightness** (20%): natural + artificial light
4. **Staging** (15%): presentation quality
5. **Cleanliness** (15%): tidiness

**Red flags** (2-7 point penalties each): flipper_gray_palette, lvp_flooring, staged_furniture, dark_interior, deferred_maintenance, ultra_wide_distortion, visible_damage, worn_finishes.

**Highlights** (2-4 point bonuses): natural_light_visible, outdoor_greenery, original_details, warm_materials, high_ceilings_visible, open_layout, quality_kitchen.

### 5.2 Sampling Strategy

Analyzes 3 photos by default (hero shot, kitchen area, secondary), with cache invalidation based on photo hash changes or 30+ day staleness.

### 5.3 Location-Agnostic

The visual scoring system is **fully location-agnostic** and works correctly for NYC listings. This is one of the strongest signals for quality assessment.

---

## 6. Scoring Engine (`services/advanced_matching.py`)

### 6.1 PropertyMatcher Class

The core intelligence layer that scores listings against buyer criteria. The scoring pipeline:

1. **Hard filters** (pass/fail): price_max, bedrooms_min, bathrooms_min, sqft_min, neighborhoods whitelist, inactive status exclusion.

2. **Additional hard filters**: dark interior signals (without offsetting light signals), busy street flag, low tranquility (<40), layout red flags (railroad, awkward), no parking.

3. **17 weighted criteria** scored 0-10 each, multiplied by weight:

| Criterion | Weight | Scoring Method |
|-----------|--------|----------------|
| natural_light | 15 | NLP hits + light_potential + visual_brightness, blended average |
| pet_friendly | 14 | **NOT IMPLEMENTED** - weight exists but no scoring logic |
| character_soul | 10 | NLP character + quality hits + year_built bonus (pre-1910: +2, pre-1940: +1) |
| location_quiet | 10 | Tranquility score + busy street penalty + noise hits + location modifiers |
| kitchen_quality | 8 | NLP kitchen keyword hits |
| gym_fitness | 10 | **NOT IMPLEMENTED** - weight exists but no scoring logic |
| outdoor_space | 8 | NLP outdoor hits + outdoor_space flag |
| high_ceilings | 6 | Ceiling keyword flag + explicit height mentions ("10 ft", "11 ft") |
| layout_intelligence | 6 | Layout keyword hits |
| in_unit_laundry | 5 | In-unit laundry keywords (full score) or building laundry (4.0) |
| views | 3 | View keyword flag |
| building_quality | 6 | **NOT IMPLEMENTED** |
| doorman_concierge | 4 | **NOT IMPLEMENTED** |
| storage | 4 | Storage keyword flag |
| move_in_ready | 4 | Move-in keywords + visual_quality_score, with flipper/condition penalties |
| central_hvac | 2 | HVAC keyword hits |
| dishwasher | 2 | Dishwasher keyword hits |

4. **Soft-cap penalties**: Price above $7,500/mo ideal incurs a linear penalty up to 10 points at the $9,500 hard cap. HOA above $1,000 penalizes 10 points.

5. **Scorecard generation**: Top 3 contributing criteria become `top_positives`. Lowest-scoring weighted criterion becomes the `key_tradeoff`. Price/HOA penalties noted.

6. **Tier assignment**: Exceptional (100+), Strong (88+), Interesting (76+), Pass.

7. **Why Now**: Price drops, new listings (<7 DOM), overlooked listings (>45 DOM), back on market.

### 6.2 NLP Signal Multipliers

Each NLP signal group has a weight multiplier from the YAML config that amplifies or attenuates the base score:
- **Positive**: light (1.5x), pet (1.8x), gym (1.4x), outdoor (1.3x), character (1.3x), kitchen (1.2x), quality (1.2x), amenities (1.1x)
- **Negative**: gross_highrise (0.5x), dark (0.5x), noise (0.6x), condition (0.5x), no_pets (0.0x = instant fail), railroad (0.4x)

### 6.3 Text Intelligence Enhancement

For listings with descriptions (40+ words), the `text_intelligence.py` module calls OpenAI to:
- Extract criterion-specific hints with confidence levels and verbatim evidence
- Identify tradeoff candidates (e.g., "no outdoor space", "busy street")
- Generate top positive candidates
- Surface red flags
- Provide timing insights

High-scoring listings (90+ points) use a more capable model (`OPENAI_TEXT_MODEL_HARD`).

### 6.4 Scoring Gaps

- **4 criteria are weighted but have NO scoring logic**: pet_friendly (14), gym_fitness (10), building_quality (6), doorman_concierge (4). These represent **34 out of 126 total points** (27%) that can never be earned.
- **Max achievable score is ~92/126 (73%)** because 34 points are unreachable, which means even a perfect listing cannot score above "Interesting" tier.
- **Tranquility score is meaningless for NYC** because geospatial module uses SF data.
- **Parking scoring** is less relevant for NYC rentals (most don't have parking), yet it's included in hard filters ("no parking" = fail).
- **Gas stove and office space** criteria exist in the scoring engine but have 0 weight in the NYC YAML, so they're inactive. This is correct behavior.

---

## 7. Weight Learning System (`services/weight_learning.py`)

### 7.1 Feedback-Driven Personalization

Users can like/dislike listings through the API. The weight learning system analyzes this feedback to adjust scoring weights:

- Requires minimum 5 signals (3 likes + 2 dislikes) before activating
- For liked listings: identifies top-scoring criteria and boosts their weights
- For disliked listings: identifies top-scoring criteria and reduces their weights
- Bounded deltas: each feedback signal adjusts weight by 5% of base, with multiplier constrained to 0.5x-2.0x

### 7.2 Integration

Learned weights are stored on the User model and applied through `PropertyMatcher`'s `user_weights` parameter. The `/matches/user/{user_id}` endpoint automatically uses learned weights.

---

## 8. Alert System

### 8.1 Event-Driven Alerts (`services/listing_alerts.py`)

After each ingestion, `process_listing_alerts()` evaluates new `ListingEvent` records:
- **New listings** scoring above threshold (76%) trigger immediate alerts
- **Price drops** >= 5% trigger immediate alerts; >= 3% trigger digest alerts
- **Back on market** triggers immediate alerts
- **Stale listings** (DOM >= 45) trigger digest alerts

### 8.2 Delivery Channels (`services/alerts.py`)

Four delivery channels with graceful degradation:
1. **iMessage** (macOS osascript)
2. **SMS** (Twilio)
3. **Email** (SMTP)
4. **Webhook** (HTTP POST)

Currently configured: iMessage to phone number, email to inbox.

---

## 9. Frontend

React 18 + TypeScript + Vite with:
- `/matches` - Scored listing feed with DossierCard components
- `/listings/:id` - Detail view with ImageGallery, feature scores
- `/criteria` - Buyer preference configuration
- React Query hooks for data fetching
- Design system with CSS tokens
- Agentation toolbar in dev mode

---

## 10. Database Schema

`PropertyListing` model has 90+ columns including:
- **Core**: address, price, beds, baths, sqft, property_type, url, lat/lon, year_built
- **13 boolean feature flags**: has_natural_light_keywords, has_high_ceiling_keywords, has_outdoor_space_keywords, etc.
- **Red flags**: has_busy_street_keywords, has_foundation_issues_keywords, is_north_facing_only, is_basement_unit
- **Scoring fields**: match_score, feature_scores (JSON), score_points, score_tier
- **Intelligence**: tranquility_score, light_potential_score, visual_quality_score, visual_assessment
- **Deduplication**: UniqueConstraint on (source, source_listing_id)

Change tracking via `ListingSnapshot` and `ListingEvent` models for price drop detection, status changes, and photo/description updates.

---

## 11. Observed Runtime Behavior

From actual ingestion runs during development:

### Run 1 (broad `new-york-ny` slug):
- Problem: Returned listings from Jamaica Queens, Staten Island, and other irrelevant areas
- Fix: Switched to 16 specific neighborhood slugs

### Run 2 (multi-location with pagination bug):
- Problem: Only Williamsburg listings came through despite configuring 16 neighborhoods
- Root cause: Pagination state tracking in `search_page()` was broken for multi-location iteration
- Fix: Rewrote to use `search_all_locations()` method that explicitly iterates all slugs

### Run 3 (neighborhood tagging issue):
- Problem: All listings showed "Brooklyn" or "New York" as neighborhood, not specific areas
- Root cause: ZenRows API returns generic borough names
- Fix: Added `SLUG_TO_NEIGHBORHOOD` mapping (26 entries) to tag from search slug

### Run 4 (detail enrichment override):
- Problem: Even after tagging, neighborhoods reverted to "Brooklyn" after detail enrichment
- Root cause: `listing_to_add.update()` overwrote the tagged neighborhood with the detail response's generic borough
- Fix: Added preservation logic to save/restore neighborhood during enrichment

### Final successful run:
- 334 unique listings across 15 neighborhoods
- 122 listings within budget ($5K-$9.5K)
- 61 listings scored as matches
- Max score: 44/126 (35%) - very low due to 34 unreachable points and limited descriptions
- Only 24 listings had descriptions (limited detail enrichment)

---

## 12. Configuration Files

### `.env.local` (active configuration)
```
DATABASE_URL=sqlite:///./.local/sherlock.db
ZENROWS_API_KEY=<key>
ANTHROPIC_API_KEY=<key>
OPENAI_API_KEY=<key>
SEARCH_MODE=rent
SEARCH_LOCATIONS=williamsburg-brooklyn-new-york-ny,west-village-new-york-ny,...(16 total)
SEARCH_PRICE_MIN=5000
SEARCH_PRICE_MAX=9500
SEARCH_BEDS_MIN=1
SEARCH_BATHS_MIN=1
SEARCH_SQFT_MIN=500
MAX_PAGES=20
MAX_DETAIL_CALLS=100
BUYER_CRITERIA_PATH=config/nyc_rental_criteria.yaml
IMESSAGE_ENABLED=true
```

### `config/nyc_rental_criteria.yaml`
- 27 target neighborhoods (Brooklyn + Manhattan)
- 126-point weighted scoring across 17 criteria
- 7 positive NLP signal groups with weight multipliers
- 6 negative NLP signal groups
- NYC-specific street boosters and penalties
- Alert thresholds for new listings, price drops, and back-on-market events
- Visual scoring preferences (boost: natural light visible, penalize: ultra-wide distortion)

---

## 13. Critical Issues Summary (Prioritized)

### P0: Blocking correctness
1. **4 criteria (34 points / 27%) have no scoring logic** - pet_friendly, gym_fitness, building_quality, doorman_concierge are weighted in YAML but have no corresponding code in `_score_listing()`. Max achievable score is 73%.
2. **Geospatial module is SF-locked** - All tranquility scores are meaningless (always ~100) for NYC listings. The "low tranquility" hard filter (<40) never triggers.

### P1: Significantly degrading effectiveness
3. **Only 7% of listings have descriptions** (24/334) - Detail enrichment is limited by MAX_DETAIL_CALLS and wasted on duplicate listings.
4. **No deduplication before detail calls** - API credits spent on listings already in the DB.
5. ~~**No StreetEasy integration**~~ - **RESOLVED**: StreetEasy provider implemented (`app/providers/streeteasy.py`), active in `INGESTION_SOURCES`.
6. **SF-specific keywords in NLP** - busy_street keywords include SF streets (van ness, geary, 19th avenue).

### P2: Limiting quality
7. **Parking hard filter in NYC** - "No parking" fails listings in a city where most rentals have no parking.
8. **HOA penalty for rentals** - HOA scoring is irrelevant for rentals.
9. **Year-built bonus calibration** - Pre-1910 bonus works for SF Victorian/Edwardian homes but needs recalibration for NYC (pre-war = 1920s-1940s).
10. **No floor-level intelligence** - NYC listing descriptions often mention floor number, which strongly correlates with light, noise, and views.
11. **No building amenity aggregation** - In NYC rentals, amenities (gym, doorman, rooftop, laundry) are building-level features that could be scraped from building profiles.

---

## 14. Data Sources Research

### ZenRows Capabilities
- **Zillow**: Full dedicated support (discovery + property detail endpoints). Currently used.
- **Idealista**: Full dedicated support but irrelevant for US markets (Spain, Italy, Portugal).
- **Other platforms**: ZenRows has a general web scraping API that could scrape any site, but no dedicated real estate endpoints for StreetEasy, Apartments.com, Rentals.com, etc.

### Alternative data sources for NYC rentals
- **StreetEasy**: Dominant NYC rental platform. Would need RapidAPI integration (StreetEasy API or Reasier) or general web scraping.
- **Apartments.com / Rent.com**: Large rental databases with API access via RapidAPI.
- **RentHop**: NYC-specific with quality scoring.
- **Listings Project**: Curated NYC listings, more character-oriented apartments.

---

## 15. What Would Make This 10x Better

### Tier 1: Fix the broken fundamentals
- Wire pet_friendly, gym_fitness, building_quality, doorman_concierge into scoring
- Replace SF geospatial data with NYC noise sources (BQE, subway lines, FDR Drive, firehouses)
- Deduplicate before detail calls to maximize description coverage
- Remove/adapt SF-specific NLP keywords

### Tier 2: Expand intelligence
- Add StreetEasy as a data source
- Extract floor number from descriptions for light/noise/view inference
- Add subway proximity scoring (walking distance to nearest station)
- Implement building-level amenity aggregation
- Add neighborhood quality signals (walkability, restaurant density, park proximity)

### Tier 3: Personalization and discovery
- Implement "similar listings" based on scored feature profiles
- Add "this listing is like X but with better Y" comparative narratives
- Build a virtual tour scheduler integration
- Add availability window matching (April/May 2026 move-in)
- Implement multi-criteria alerts ("notify me when a Williamsburg loft with in-unit laundry drops below $7K")

---

*Document generated 2026-02-21 from codebase at ~/home-hog*
