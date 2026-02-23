# Scoring Deep Dive (NYC Rental) - February 22, 2026

## Scope
This document captures a full investigation of how Sherlock Homes currently ranks listings for NYC rentals, and what high/medium/low scores mean in practice.

The analysis combines:
- code-path inspection (matching, NLP, geospatial, criteria loading, ranking, explainability)
- runtime diagnostics against a local SQLite snapshot (`homehog.db` in that run; current default is `.local/sherlock.db`) on February 22, 2026

## Runtime Context Used
- `SEARCH_MODE=rent` (`.env.local`)
- `BUYER_CRITERIA_PATH=config/nyc_rental_criteria.yaml` (`.env.local`)
- Active weights sum: `117` points (`config/nyc_rental_criteria.yaml`)
- Local dataset size: `328` listings

## End-to-End Decision Pipeline
1. Load criteria config and effective weights.
2. Apply hard filters (price, beds, baths, sqft, neighborhood, status).
3. Build listing context:
   - NLP hits from `analyze_text_signals`
   - tranquility score (if available)
4. Apply additional hard filters:
   - dark-without-light
   - busy street and low tranquility
   - layout red flags
   - rent-mode no-pets disqualification
5. Score weighted components (0-10 per criterion, scaled by weights).
6. Apply penalties:
   - soft price penalty (rent currently uses this)
   - HOA penalty (disabled in rent mode)
7. Rank descending by total points and return top matches.

Primary implementation:
- `app/services/advanced_matching.py`
- `app/services/scoring/primitives.py`
- `app/services/nlp.py`
- `app/services/geospatial.py`

## Scoring Math
For each criterion:
- `criterion_points = (criterion_score_0_to_10 / 10) * criterion_weight`

Total:
- `total_points = sum(criterion_points) - price_penalty - hoa_penalty`

Percent:
- `score_percent = (total_points / total_possible_points) * 100`
- `total_possible_points = sum(effective_weights) = 117` (current setup)

Tier labels:
- `>= 80`: Exceptional
- `>= 70`: Strong
- `>= 60`: Interesting
- `< 60`: Pass

## What Happened on Current Data Snapshot

### Funnel
- Total listings: `328`
- Passed hard filters: `11`
- Passed additional hard filters: `7`

Hard-fail reason counts (a listing can fail multiple reasons):
- bedrooms below min: `176`
- bathrooms below min: `243`
- sqft below min: `233`
- price above max: `43`

Additional-fail reason counts:
- no pets allowed: `2`
- busy street signal: `2`

### Score Distribution
Among final ranked listings (`7` listings):
- min: `22.07`
- p25: `31.93`
- median: `37.43`
- p75: `43.53`
- max: `46.15`
- mean: `36.65`

Tier result:
- Exceptional: `0`
- Strong: `0`
- Interesting: `0`
- Pass: `7`

### Notable Runtime Signals
- Tranquility present among hard-pass listings: `0`
- Tranquility missing among hard-pass listings: `11`

Reason:
- geospatial tranquility is SF-bounded and returns `None` outside SF.
- For NYC listings, location quiet usually starts from neutral baseline in scoring.

### Average Criterion Impact (among ranked listings)
Largest average point contributors:
- natural_light: `8.65`
- character_soul: `7.57`
- location_quiet: `4.79`
- outdoor_space: `4.51`
- kitchen_quality: `4.11`

High configured weights with low observed activation:
- pet_friendly (weight 14): avg `2.0` points
- gym_fitness (weight 12): avg `1.71` points

## Qualitative Meaning: High / Medium / Low

## Absolute (Configured) Meaning
With `117` total possible points:
- 60% (Interesting) = `70.2` points
- 70% (Strong) = `81.9` points
- 80% (Exceptional) = `93.6` points

Interpretation:
- The current rubric expects broad excellence across many categories, not only must-haves.

## Practical (Current Data) Meaning
Given current market feed + metadata completeness, the observed ranked band is much lower.

Working practical bands (for current state):
- High relative: `~42-46%`
- Medium relative: `~32-41%`
- Low relative: `~22-31%`

So today, top-of-list visually strong apartments can still show "Pass" tier numerically.

## Concrete Profiles

High relative (current top cohort):
- Very strong light, character, and at least one lifestyle pillar (outdoor or kitchen)
- Usually no hard red flags
- Still often missing multiple high-weight categories (pet/gym/doorman/etc)
- Often lands in low-to-mid 40% range

Medium relative:
- Good in 2-3 major criteria but partial blanks in many weighted buckets
- Some penalty drag from price soft-cap
- Lands in 30s

Low relative (still passing filters):
- One strong anchor criterion (example: gym) but weak coverage elsewhere
- Little depth across weighted criteria
- Lands in low 20s to low 30s

## System Behaviors Worth Calling Out
1. Hard filters are decisive right now.
   - Only 11/328 survive hard filters.
   - Sparse/missing fields (especially sqft) materially reduce candidate pool.

2. Current tier labels are calibrated above observed market outcomes.
   - All ranked listings currently label as `Pass`.

3. NYC quiet scoring is currently only partly meaningful.
   - SF-only tranquility integration means no tranquility-based uplift in NYC.

4. Explainability text can be post-edited after scoring.
   - LLM enrichment can replace top positives/tradeoffs, which may diverge from pure score math.

5. Config/implementation gaps still exist.
   - Negative signal key mismatch: config uses `noise`, scorer currently reads `location_noise`.
   - `above_restaurant` appears in config penalties but is not implemented in location modifiers logic.

6. Matcher currently ignores the passed `criteria` object and always loads config path.
   - `self.criteria` is stored but not consumed in scoring path.

## Exploration Backlog (What to Take to Next Level)
1. Calibration track:
   - Decide whether tiers should be absolute targets or distribution-aware.
   - If distribution-aware, define percentile-based tiers and monitor drift.

2. Criteria coherence track:
   - Align config keys and scorer consumption (`noise` vs `location_noise`).
   - Implement missing penalty conditions that are declared in config.

3. Candidate funnel track:
   - Revisit hard-filter behavior for missing fields (especially sqft).
   - Consider unknown-data handling vs binary exclusion.

4. NYC location intelligence track:
   - Replace SF-bounded tranquility model or disable that feature in NYC mode.
   - Keep location modifiers but ensure coverage and evidence quality.

5. Explainability trust track:
   - Define precedence between score-derived reasons and LLM-updated narrative.
   - Preserve score-grounded traceability in output payloads.

6. Weight learning track:
   - Start collecting enough feedback signals to activate learned multipliers.
   - Reassess ranking behavior once user-adaptive weights are non-empty.

## Suggested Success Metrics for the Next Iteration
- Match quality:
  - top-10 manual relevance rating from user review sessions
- Calibration:
  - correlation between score bands and user keep/reject actions
- Coverage:
  - share of candidates passing hard filters
- Signal health:
  - activation rate per high-weight criterion
- Trust:
  - consistency between displayed reasons and score contributions
