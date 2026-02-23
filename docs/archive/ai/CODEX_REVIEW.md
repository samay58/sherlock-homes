# Codex Review: NYC Scoring Overhaul

## What happened

8 changes were made across 7 files to take Sherlock Homes from SF-only scoring to NYC rental support. The changes were implemented in a single session. All 11 existing tests pass, and basic import/syntax checks pass. No runtime testing against live data has been done yet.

## Your job

Do a thorough code review of every change. Look for bugs, logic errors, missed edge cases, stale references to SF that should have been updated, and anything that smells like it was slapped in without thought. Fix what you find. Don't add comments or docstrings. Don't refactor code that wasn't touched by these changes.

## Files changed (read all of these)

1. `app/services/geospatial.py` - Added `_is_in_sf()` bounding box check. `calculate_tranquility_score()` now returns `score: None` for non-SF locations.
2. `app/services/nlp.py` - Added 5 keyword categories (pet_friendly, no_pets, gym_fitness, doorman_concierge, building_quality). Replaced 7 SF street names in busy_street with 9 NYC equivalents. Updated `extract_flags()` valid lists.
3. `app/models/listing.py` - Added 5 boolean columns (is_pet_friendly, is_no_pets, has_gym_keywords, has_doorman_keywords, has_building_quality_keywords).
4. `app/services/persistence.py` - Added 5 flag-to-column mappings in the `valid_flags` dict.
5. `app/services/scoring/primitives.py` - Added 4 criterion labels. Changed `TIER_THRESHOLDS` from raw points (100/88/76/0) to percentages (80/70/60/0). Changed `_score_tier()` param name from `total_points` to `score_percent`.
6. `app/services/advanced_matching.py` - Biggest changeset. Added `from app.core.config import settings`. Added 4 new scoring blocks (pet_friendly, gym_fitness, building_quality, doorman_concierge) after storage block. Changed year-built bonus from pre-1910/pre-1940 to pre-1940/pre-1960. Wrapped no-parking hard filter with `settings.SEARCH_MODE != "rent"`. Added `is_no_pets` hard filter for rent mode. Wrapped HOA penalty with rent mode guard. Changed `_score_tier()` call to pass `score_percent_value` instead of `total_points`.
7. `app/services/ingestion.py` - Added dedup step before `_enrich_summaries()`. Dedupes by `(source, source_listing_id)` tuple. Sorts unique summaries: in-budget first, then by photo count descending.

## Specific things to check

### Correctness

- **Tranquility None propagation**: `calculate_tranquility_score` now returns `score: None` for non-SF. Trace every caller. In `ingestion.py:163`, the result is stored as `listing_to_add["tranquility_score"] = tranquility["score"]` which will be `None`. In `advanced_matching.py:324-332`, the `_score_listing` method calls `calculate_tranquility_score` and checks `tranquility.get("score")`. If that's `None`, `tranquility_score` stays `None`, and the quiet score defaults to 5.0 (neutral). Verify this path is actually safe and no downstream code does arithmetic on `None`.

- **`_score_tier` callers**: The function signature changed from accepting raw points to percentage. Search for ALL callers of `_score_tier` to make sure none still pass raw points. There's one call in `_apply_scorecard` (line 294) which now correctly passes `score_percent_value`. Are there any other callers?

- **`TOTAL_POINTS = 126` constant** on line 42 of advanced_matching.py. This is a fallback that's used when `sum(self._effective_weights.values())` is 0. The NYC YAML weights sum to 117, not 126. The constant is only used as a fallback (`or TOTAL_POINTS`) so it shouldn't matter in practice, but verify it's truly unreachable when weights are loaded.

- **Dedup key correctness**: The dedup in ingestion.py uses `(s.get("source"), s.get("source_listing_id"))` as the key. If `source_listing_id` is None for some summaries (which `_apply_source_fields` tries to set from `listing_id`), the dedup key becomes `("zillow", None)` and only one such listing survives. Check whether `_apply_source_fields` guarantees `source_listing_id` is set before the dedup runs.

- **Sort lambda closure**: The sort in ingestion.py uses `lambda s: (...)` which captures `price_max` from the enclosing scope. This is fine, but check that the lambda doesn't shadow the loop variable `s` from the dedup loop above it (it doesn't since the dedup loop is finished, but verify).

### Edge cases

- **`is_no_pets` column**: The hard filter checks `listing.is_no_pets` which defaults to `False`. For listings already in the DB before this change (without the column), SQLite will return `None` for the missing column until the DB is nuked. The `if settings.SEARCH_MODE == "rent" and listing.is_no_pets:` check treats `None` as falsy, so it won't incorrectly filter. But verify this is the intended behavior for the transition period.

- **Pet scoring when no_pets weight is 0.0**: The YAML has `no_pets: weight: 0.0`. In the pet_friendly scoring block, `no_pets_multiplier` will be `0.0`, so `pet_score * 0.0 = 0.0`. This zeroes out the pet score when no_pets keywords are found. But the listing already gets hard-filtered by the no_pets check in `_passes_additional_hard_filters`. So the multiplier is dead code for rent mode. Is this intentional redundancy or a sign the logic is confused? If the listing passes hard filters (no_pets not detected), the multiplier never fires. If no_pets IS detected, the listing is already rejected. The only scenario where the multiplier matters is in buy mode where the hard filter doesn't apply. Verify this is acceptable.

- **building_quality reuses quality_hits from character_soul**: The building_quality scoring block reads `bq_hits = nlp_hits.get("positive_hits", {}).get("quality", [])`. The character_soul block also reads from `quality_hits` (same source). This means quality keyword hits contribute to BOTH character_soul and building_quality scores. Is this double-counting intentional? The YAML "quality" group has keywords like "luxury", "boutique building", "well-maintained". Some of these are architectural character, others are building quality. Maybe the building_quality block should not reuse quality_hits and instead only rely on the `has_building_quality_keywords` flag and `visual_quality_score`.

- **doorman scoring bypass**: The doorman block checks `listing.has_doorman_keywords` (set by NLP flag extraction from `KEYWORDS["doorman_concierge"]`). Then it ALSO checks amenity_hits from the YAML `amenities` group, filtering for doorman-specific terms. Then it checks raw `text_lower` for "24-hour doorman" and "full-time doorman". The raw text check can override the NLP score to 10.0 even if the flag wasn't set. Is this correct? The NLP keywords list already includes "24-hour doorman" and "full-time doorman" so the flag should be set in that case. The raw text check is redundant but harmless. Verify.

### Stale SF references that may need updating

- `app/services/geospatial.py` still has `is_on_busy_street()` and `is_near_freeway()` functions that use SF data. Are these called anywhere? If they're called for NYC listings they'll return false (no SF streets nearby) which is technically correct but useless.

- `nlp.py` view keywords still reference SF landmarks: "golden gate", "coit tower", "alcatraz view", "twin peaks". These won't match NYC listings (harmless) but it's sloppy. Consider whether to swap for NYC equivalents (central park, hudson river, brooklyn bridge, empire state, etc.) or just leave them since they produce no false positives.

- `nlp.py` KEYWORDS still has "seismic", "retrofit needed", "soft story" in foundation_issues. These are SF earthquake terms. They won't match NYC listings but they're dead keywords.

- The comment at the top of `nlp.py` `KEYWORDS["pet_friendly"]` section says `# Red Flags (negative indicators)` because it was inserted right before `busy_street` which had that comment. The comment now incorrectly labels pet_friendly as a red flag. Fix the comment placement.

### Style / quality

- The 4 new scoring blocks in advanced_matching.py follow the same pattern as existing blocks (good) but are more verbose. Check if any of the evidence-building or multiplier logic can be tightened without changing behavior.

- The `nlp.py` KEYWORDS dict now has 22 entries. The new entries (pet_friendly, no_pets, etc.) are interleaved right before busy_street because that's where the insertion point was. This puts positive features (pet_friendly, gym_fitness, doorman_concierge, building_quality) mixed in with negative indicators (no_pets, busy_street). Not a bug but the organization is messy. Consider whether reordering matters for readability.

## Config files to cross-reference

- `config/nyc_rental_criteria.yaml` - The active buyer config. Has weights for all 4 new criteria plus NLP signals for pet, gym, amenities, quality, gross_highrise, no_pets.
- `.env.local` - Sets `SEARCH_MODE=rent`, `BUYER_CRITERIA_PATH=config/nyc_rental_criteria.yaml`.

## Tests

Run `cd /Users/samaydhawan/home-hog && .venv/bin/python -m pytest tests/ -v` to verify existing tests still pass after any fixes.

## Rules

- Fix bugs and logic errors you find. Don't ask, just fix.
- Don't add docstrings, comments, or type annotations to code you didn't change.
- Don't refactor working code that wasn't part of this changeset.
- Don't create new test files unless you find a bug that needs a regression test.
- Keep fixes minimal and targeted.
