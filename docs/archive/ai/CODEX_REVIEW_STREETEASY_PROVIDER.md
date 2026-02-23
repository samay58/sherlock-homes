# Codex Review: StreetEasy Provider + Codebase Quality Audit

## What happened

A new `StreetEasyProvider` was added to ingest NYC rental listings via ZenRows universal scraping. Three files were changed:

- `app/providers/streeteasy.py` (new, 314 lines)
- `app/providers/registry.py` (added import + registry entry)
- `app/core/config.py` (added `STREETEASY_SEARCH_URLS` setting)

The provider follows the same pattern as `CraigslistProvider` and `TruliaProvider`: use `ZenRowsUniversalClient` for HTTP, BeautifulSoup for parsing, return dicts that map to `PropertyListing` fields.

## What to investigate

### 1. StreetEasy provider correctness

Read `app/providers/streeteasy.py` end-to-end and verify:

- **Protocol compliance**: Does it satisfy `BaseProvider` in `app/providers/base.py`? The `search()` and `get_details()` signatures must match.
- **Return dict keys**: Compare the keys returned by `search()` and `get_details()` against what `app/services/ingestion.py` expects. Read ingestion.py to see which fields it reads from provider output. Flag any mismatches (wrong key names, missing required fields, extra fields that get silently dropped).
- **Amenity flag names**: The provider sets `has_doorman`, `has_elevator`, `has_gym`, `has_laundry`, `has_parking`, `has_dishwasher`, `has_roof_deck`, `has_outdoor_space`. Verify these match the actual column names on `PropertyListing` in `app/models/listing.py`. If the model uses different names (e.g., `doorman` vs `has_doorman`), the flags will be silently lost.
- **`search_page()` interface**: Ingestion calls `search_page()` if it exists (check `app/services/ingestion.py`). Verify the return signature `(list, bool)` matches what ingestion expects.
- **Pagination logic**: The provider caps at 5 pages and assumes more pages exist if results are non-empty. Is this sound? Compare with how Zillow's `search_all_locations()` handles pagination.
- **Error handling**: The provider catches broad `Exception` in search and returns empty. Is this consistent with other providers or too aggressive?
- **`_extract_card_data` lambda**: There's a complex lambda in `soup.find("a", href=lambda ...)`. Verify it handles edge cases (None href, relative vs absolute URLs, URL fragments).

### 2. Ingestion pipeline integration

Read `app/services/ingestion.py` and trace the path a StreetEasy listing takes:

- How does ingestion decide whether to call `search_page()` vs `search()`?
- After search results come back, how are they deduped? The dedup key is `(source, source_listing_id)`. For StreetEasy, `source_listing_id` is the full URL. Is this stable across runs? (URL query params, trailing slashes, etc.)
- When `get_details()` returns, how are the dict fields mapped onto `PropertyListing`? Is there a normalization step that would catch misnamed keys?
- Does the ingestion pipeline handle the case where `STREETEASY_SEARCH_URLS` is empty (no URLs configured)? The provider would have `self._search_urls = []` and `search()` would return an empty list. Confirm this is graceful.

### 3. Scoring compatibility

Read `app/services/advanced_matching.py` and `config/user_criteria.yaml` (or `config/nyc_rental_criteria.yaml`):

- Do StreetEasy-sourced listings get scored correctly? Are there any source-specific code paths that would skip streeteasy?
- The amenity flags extracted by the provider (doorman, elevator, outdoor space, etc.) should feed into scoring criteria. Trace the path from `PropertyListing.has_doorman` (or whatever the column is) through to scoring weight application.

### 4. CLAUDE.md accuracy

Read `CLAUDE.md` in the repo root. It documents the architecture, key files, and patterns. After understanding the StreetEasy addition:

- Update the Key Files table if needed.
- Check that the Architecture section's description of providers and ingestion is still accurate.
- Verify that the "Configuration" section's example env vars reflect the new `STREETEASY_SEARCH_URLS` setting.
- Remove any stale or misleading statements.
- Keep the doc tight. No filler, no promotional language, no "comprehensive" or "robust" adjectives. State facts.

### 5. Code quality pass on streeteasy.py

- Are there dead code paths or unreachable branches?
- Are the CSS selectors reasonable? StreetEasy redesigns periodically. The selectors should be broad enough to survive minor DOM changes (using comma-separated fallbacks) but specific enough to avoid false matches.
- Is the `SLUG_TO_NEIGHBORHOOD` dict complete for the neighborhoods configured in `.env.local`?
- Any obvious bugs in regex patterns?

### 6. Cross-provider consistency

Compare `streeteasy.py` against `craigslist.py` and `trulia.py`:

- Are there inconsistencies in how `source_listing_id` is set?
- Do all providers handle the `close()` method the same way?
- Is error handling consistent across providers?

## Files to read (in order)

1. `app/providers/base.py`
2. `app/providers/streeteasy.py`
3. `app/models/listing.py`
4. `app/services/ingestion.py`
5. `app/services/advanced_matching.py`
6. `app/providers/craigslist.py`
7. `app/providers/trulia.py`
8. `config/user_criteria.yaml` or `config/nyc_rental_criteria.yaml`
9. `CLAUDE.md`

## Output format

Produce a single list of findings, grouped by severity:

- **Bugs**: Things that will break at runtime or produce wrong results.
- **Gaps**: Missing handling that could cause silent data loss or incorrect scoring.
- **Cleanup**: Style issues, dead code, inconsistencies that should be fixed but won't break anything.

For each finding, state the file, line range, what's wrong, and the fix. If you fix something, do it inline. If a fix requires a design decision, describe the options and leave it.
