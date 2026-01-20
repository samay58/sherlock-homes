import asyncio
import logging
import sys
from datetime import datetime, timezone # Import datetime
from typing import List, Dict, Any, Tuple

# Local modules
from app.core.config import settings
from app.providers.registry import get_active_providers
from app.services.persistence import upsert_listings
from app.services.nlp import extract_flags, estimate_light_potential
from app.services.geospatial import calculate_tranquility_score
from app.services.neighborhoods import resolve_neighborhood
from app.services.listing_alerts import process_listing_alerts
from app.state import ingestion_state # Import shared state

logger = logging.getLogger(__name__)

SF_BBOX = (37.707, -122.515, 37.83, -122.355)  # lat_sw, lon_sw, lat_ne, lon_ne
TILE_LAT_STEP = 0.02
TILE_LON_STEP = 0.02


def _apply_source_fields(listing: Dict[str, Any], source_key: str) -> Dict[str, Any]:
    if not listing.get("source"):
        listing["source"] = source_key
    if listing.get("source_listing_id") is None and listing.get("listing_id") is not None:
        listing["source_listing_id"] = str(listing["listing_id"])
    return listing


def _generate_tiles(bbox: Tuple[float, float, float, float]):
    lat_lo, lon_lo, lat_hi, lon_hi = bbox
    lat = lat_lo
    while lat < lat_hi:
        lon = lon_lo
        while lon < lon_hi:
            yield (lat, lon, min(lat + TILE_LAT_STEP, lat_hi), min(lon + TILE_LON_STEP, lon_hi))
            lon += TILE_LON_STEP
        lat += TILE_LAT_STEP


async def run_ingestion_job():
    # ---> Record Start Time & Clear State <---
    start_time = datetime.now(timezone.utc)
    ingestion_state.last_run_start_time = start_time
    ingestion_state.last_run_end_time = None
    ingestion_state.last_run_summary_count = 0
    ingestion_state.last_run_detail_calls = 0
    ingestion_state.last_run_upsert_count = 0
    ingestion_state.last_run_error = None
    logger.info(f"Starting ingestion job at {start_time.isoformat()}Z")

    providers = get_active_providers()
    try:
        summary_count_total = 0
        detail_calls_total = 0
        upsert_total = 0
        all_enriched: List[Dict[str, Any]] = []

        for spec in providers:
            provider = spec.factory()
            provider_summaries: List[Dict[str, Any]] = []
            provider_enriched: List[Dict[str, Any]] = []
            try:
                # ---> Fetch summaries <---
                try:
                    page = 1
                    max_pages = settings.MAX_PAGES
                    logger.info(
                        "Fetching up to %d pages from %s (MAX_PAGES=%d)",
                        max_pages,
                        spec.key,
                        max_pages,
                    )
                    while page <= max_pages:
                        if hasattr(provider, "search_page"):
                            batch, more = await provider.search_page(page=page)
                        else:
                            batch = await provider.search(bbox=None, page=page)
                            more = False
                        provider_summaries.extend([_apply_source_fields(item, spec.key) for item in batch])
                        if not more:
                            break
                        await asyncio.sleep(1.5)  # polite pause for ZenRows quota
                        page += 1
                    summary_count_total += len(provider_summaries)
                except Exception as e:
                    logger.error(
                        "Error fetching %s listing summaries: %s",
                        spec.key,
                        e,
                        exc_info=True,
                    )
                    ingestion_state.last_run_error = f"Failed during summary fetch ({spec.key}): {e}"
                    # Log and continue with potentially partial summaries

                logger.info(
                    "Fetched %d listings (raw summaries) from %s",
                    len(provider_summaries),
                    spec.key,
                )

                # ---> Enrich listings <---
                if provider_summaries:  # only proceed if we have summaries
                    detail_calls_made = 0  # Counter for detail API calls
                    max_detail_calls = settings.MAX_DETAIL_CALLS
                    logger.info(
                        "Enriching up to %d listings with full details from %s (MAX_DETAIL_CALLS=%d)",
                        max_detail_calls,
                        spec.key,
                        max_detail_calls,
                    )

                    for i, summary_listing in enumerate(provider_summaries):
                        listing_id = summary_listing.get("source_listing_id") or summary_listing.get("listing_id")
                        # print(f"---> Processing listing {i+1}/{len(provider_summaries)}, ID: {listing_id}") # Removed debug print
                        logger.debug(
                            "Processing listing %d/%d (%s), ID: %s",
                            i + 1,
                            len(provider_summaries),
                            spec.key,
                            listing_id,
                        )  # Keep debug log

                        if not listing_id:
                            logger.warning(
                                "Skipping enrichment for listing without listing_id (%s): %s",
                                spec.key,
                                summary_listing.get("address"),
                            )
                            provider_enriched.append(summary_listing)  # Add as-is if no ID
                            continue

                        listing_to_add = summary_listing.copy()

                        # ---> Check detail call limit / support ---
                        if spec.supports_details:
                            if detail_calls_made >= max_detail_calls:
                                if detail_calls_made == max_detail_calls:  # Log only once when limit is first hit
                                    logger.info(
                                        "Reached detail call limit (%d) for %s. Skipping remaining details.",
                                        max_detail_calls,
                                        spec.key,
                                    )
                                    detail_calls_made += 1  # Increment past limit to prevent re-logging
                                # Skip detail fetch for this listing, keep summary data in listing_to_add
                            else:
                                # ---> Fetch and process details (if under limit) <---
                                try:
                                    logger.debug(
                                        "Attempting to fetch details for %s: %s (Call #%d)",
                                        spec.key,
                                        listing_id,
                                        detail_calls_made + 1,
                                    )
                                    details = await provider.get_details(listing_id)
                                    detail_calls_made += 1
                                    await asyncio.sleep(0.5)  # Small polite pause between detail calls

                                    # Merge summary and details, details take precedence
                                    listing_to_add.update({k: v for k, v in details.items() if v is not None})

                                    # Ensure photos are handled correctly (prefer details photos if they exist)
                                    detail_photos = details.get("photos")
                                    if detail_photos:  # If details had photos (even empty list), use them
                                        listing_to_add["photos"] = detail_photos
                                    elif not listing_to_add.get("photos"):  # If details had no photos and summary also had none
                                        listing_to_add["photos"] = []  # Default to empty list
                                except Exception as e:
                                    logger.error(
                                        "Error fetching or processing details for %s %s: %s",
                                        spec.key,
                                        listing_id,
                                        e,
                                        exc_info=True,
                                    )
                                    # Keep summary data in listing_to_add if details fail

                        # Extract flags from description if available
                        description = listing_to_add.get("description")
                        if description:
                            listing_to_add["flags"] = extract_flags(description)
                        else:
                            listing_to_add["flags"] = {}

                        # ========================================
                        # SHERLOCK HOMES INTELLIGENCE SCORING
                        # ========================================

                        # Calculate Tranquility Score (geospatial)
                        lat = listing_to_add.get("lat")
                        lon = listing_to_add.get("lon")
                        if lat and lon:
                            try:
                                tranquility = calculate_tranquility_score(lat, lon)
                                listing_to_add["tranquility_score"] = tranquility["score"]
                                listing_to_add["tranquility_factors"] = tranquility["factors"]
                            except Exception as e:
                                logger.debug("Could not calculate tranquility for %s: %s", listing_id, e)

                        # Neighborhood normalization (use coords if needed)
                        neighborhood = listing_to_add.get("neighborhood")
                        normalized = resolve_neighborhood(neighborhood, lat, lon)
                        if normalized:
                            listing_to_add["neighborhood"] = normalized

                        # Calculate Light Potential Score (NLP)
                        flags = listing_to_add.get("flags", {})
                        try:
                            light_data = estimate_light_potential(
                                description=description,
                                is_north_facing_only=flags.get("north_facing_only", False),
                                is_basement_unit=flags.get("basement_unit", False),
                                has_natural_light_keywords=flags.get("natural_light", False),
                                photo_count=len(listing_to_add.get("photos", [])),
                            )
                            listing_to_add["light_potential_score"] = light_data["score"]
                            listing_to_add["light_potential_signals"] = light_data["signals"]
                        except Exception as e:
                            logger.debug("Could not calculate light potential for %s: %s", listing_id, e)

                        provider_enriched.append(_apply_source_fields(listing_to_add, spec.key))

                    detail_calls_total += detail_calls_made
            finally:
                try:
                    if hasattr(provider, "close"):
                        await provider.close()
                except Exception as e:
                    logger.error("Error closing %s provider: %s", spec.key, e, exc_info=True)

            if provider_enriched:
                upsert_listings(provider_enriched)
                upsert_total += len(provider_enriched)
                all_enriched.extend(provider_enriched)
                logger.info("Ingestion job upserted %d listings for %s", len(provider_enriched), spec.key)

        ingestion_state.last_run_summary_count = summary_count_total
        ingestion_state.last_run_detail_calls = detail_calls_total
        ingestion_state.last_run_upsert_count = upsert_total

        # ---> Persisted results processed: alerts ---
        if all_enriched:
            try:
                alert_stats = process_listing_alerts(start_time)
                logger.info(
                    "Alert processing complete (immediate=%d, digest=%d)",
                    alert_stats.get("immediate", 0),
                    alert_stats.get("digest", 0),
                )
            except Exception as e:
                logger.error("Alert processing failed: %s", e, exc_info=True)
        else:
            logger.warning("No listings available to upsert after enrichment phase.")

    except Exception as e: # Catch broader errors during the main process
        logger.error(f"Unhandled error during ingestion job: {e}", exc_info=True)
        ingestion_state.last_run_error = f"Unhandled error: {e}"
    finally:
        # ---> Record End Time & Ensure provider cleanup <---
        end_time = datetime.now(timezone.utc)
        ingestion_state.last_run_end_time = end_time
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Closing provider connection. Job finished at {end_time.isoformat()}Z (Duration: {duration:.2f}s)")
        # Providers are closed per-spec above.


def run_ingestion_job_sync():
    """Blocking entry for celery/apscheduler/routes."""
    asyncio.run(run_ingestion_job()) 
