import asyncio
import logging
import sys
from datetime import datetime # Import datetime
from typing import List, Dict, Any, Tuple

# Local modules
from app.core.config import settings
from app.providers.zillow import ZillowProvider
from app.services.persistence import upsert_listings
from app.services.nlp import extract_flags, estimate_light_potential
from app.services.geospatial import calculate_tranquility_score
from app.state import ingestion_state # Import shared state

logger = logging.getLogger(__name__)

SF_BBOX = (37.707, -122.515, 37.83, -122.355)  # lat_sw, lon_sw, lat_ne, lon_ne
TILE_LAT_STEP = 0.02
TILE_LON_STEP = 0.02


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
    start_time = datetime.utcnow()
    ingestion_state.last_run_start_time = start_time
    ingestion_state.last_run_end_time = None
    ingestion_state.last_run_summary_count = 0
    ingestion_state.last_run_detail_calls = 0
    ingestion_state.last_run_upsert_count = 0
    ingestion_state.last_run_error = None
    logger.info(f"Starting ingestion job at {start_time.isoformat()}Z")

    provider = ZillowProvider()
    listings_summary: List[Dict[str, Any]] = []
    enriched_listings: List[Dict[str, Any]] = []
    try:
        # ---> Fetch summaries <---
        try:
            page = 1
            max_pages = settings.MAX_PAGES
            logger.info(f"Fetching up to {max_pages} pages of listings (MAX_PAGES={max_pages})")
            while page <= max_pages:
                batch, more = await provider.search_page(page=page)
                listings_summary.extend(batch)
                if not more:
                    break
                await asyncio.sleep(1.5)  # polite pause for ZenRows quota
                page += 1
            ingestion_state.last_run_summary_count = len(listings_summary) # Store count
        except Exception as e:
            logger.error(f"Error fetching listing summaries: {e}", exc_info=True)
            ingestion_state.last_run_error = f"Failed during summary fetch: {e}"
            # Log and continue with potentially partial summaries
        
        logger.info("Fetched %d listings (raw summaries)", len(listings_summary))

        # ---> Enrich listings <---
        if listings_summary: # only proceed if we have summaries
            detail_calls_made = 0 # Counter for detail API calls
            max_detail_calls = settings.MAX_DETAIL_CALLS
            logger.info(f"Enriching up to {max_detail_calls} listings with full details (MAX_DETAIL_CALLS={max_detail_calls})")

            for i, summary_listing in enumerate(listings_summary):
                listing_id = summary_listing.get("listing_id")
                # print(f"---> Processing listing {i+1}/{len(listings_summary)}, ID: {listing_id}") # Removed debug print
                logger.debug(f"Processing listing {i+1}/{len(listings_summary)}, ID: {listing_id}") # Keep debug log
                
                if not listing_id:
                    logger.warning("Skipping enrichment for listing without listing_id: %s", summary_listing.get("address"))
                    enriched_listings.append(summary_listing) # Add as-is if no ID
                    continue
                
                listing_to_add = summary_listing.copy()

                # ---> Check detail call limit <---
                if detail_calls_made >= max_detail_calls:
                    if detail_calls_made == max_detail_calls: # Log only once when limit is first hit
                       logger.info(f"Reached detail call limit ({max_detail_calls}). Skipping details for remaining listings.")
                       detail_calls_made += 1 # Increment past limit to prevent re-logging
                    # Skip detail fetch for this listing, keep summary data in listing_to_add
                else:
                    # ---> Fetch and process details (if under limit) <---
                    try: 
                        logger.debug(f"Attempting to fetch details for ZPID: {listing_id} (Call #{detail_calls_made + 1})")
                        details = await provider.get_details(listing_id)
                        detail_calls_made += 1 
                        await asyncio.sleep(0.5) # Small polite pause between detail calls

                        # Merge summary and details, details take precedence
                        listing_to_add.update({k: v for k, v in details.items() if v is not None}) # Merge only non-None values from details
                        
                        # Ensure photos are handled correctly (prefer details photos if they exist)
                        detail_photos = details.get("photos")
                        if detail_photos: # If details had photos (even empty list), use them
                            listing_to_add["photos"] = detail_photos
                        elif not listing_to_add.get("photos"): # If details had no photos and summary also had none
                             listing_to_add["photos"] = [] # Default to empty list

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
                                logger.debug(f"Could not calculate tranquility for {listing_id}: {e}")

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
                            logger.debug(f"Could not calculate light potential for {listing_id}: {e}") 
                        
                    except Exception as e:
                         logger.error(f"Error fetching or processing details for ZPID {listing_id}: {e}", exc_info=True)
                         # Keep summary data in listing_to_add if details fail

                enriched_listings.append(listing_to_add)
            ingestion_state.last_run_detail_calls = detail_calls_made # Store count

        # ---> Persist results <---
        if enriched_listings:
             upsert_listings(enriched_listings)
             upsert_count = len(enriched_listings)
             ingestion_state.last_run_upsert_count = upsert_count # Store count
             logger.info("Ingestion job upserted %d listings", upsert_count)
        else:
             logger.warning("No listings available to upsert after enrichment phase.")

    except Exception as e: # Catch broader errors during the main process
        logger.error(f"Unhandled error during ingestion job: {e}", exc_info=True)
        ingestion_state.last_run_error = f"Unhandled error: {e}"
    finally:
        # ---> Record End Time & Ensure provider cleanup <---
        end_time = datetime.utcnow()
        ingestion_state.last_run_end_time = end_time
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Closing provider connection. Job finished at {end_time.isoformat()}Z (Duration: {duration:.2f}s)")
        try:
            await provider.close()
        except Exception as e:
            logger.error(f"Error closing provider: {e}", exc_info=True)


def run_ingestion_job_sync():
    """Blocking entry for celery/apscheduler/routes."""
    asyncio.run(run_ingestion_job()) 
