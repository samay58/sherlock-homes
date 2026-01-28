import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from app.core.config import settings
from app.providers.registry import get_active_providers
from app.services.geospatial import calculate_tranquility_score
from app.services.listing_alerts import process_listing_alerts
from app.services.neighborhoods import resolve_neighborhood
from app.services.nlp import estimate_light_potential, extract_flags
from app.services.persistence import upsert_listings
from app.state import ingestion_state

logger = logging.getLogger(__name__)

SF_BBOX = (37.707, -122.515, 37.83, -122.355)  # lat_sw, lon_sw, lat_ne, lon_ne
TILE_LAT_STEP = 0.02
TILE_LON_STEP = 0.02


def _apply_source_fields(listing: Dict[str, Any], source_key: str) -> Dict[str, Any]:
    if not listing.get("source"):
        listing["source"] = source_key
    if (
        listing.get("source_listing_id") is None
        and listing.get("listing_id") is not None
    ):
        listing["source_listing_id"] = str(listing["listing_id"])
    return listing


def _generate_tiles(bbox: Tuple[float, float, float, float]):
    lat_lo, lon_lo, lat_hi, lon_hi = bbox
    lat = lat_lo
    while lat < lat_hi:
        lon = lon_lo
        while lon < lon_hi:
            yield (
                lat,
                lon,
                min(lat + TILE_LAT_STEP, lat_hi),
                min(lon + TILE_LON_STEP, lon_hi),
            )
            lon += TILE_LON_STEP
        lat += TILE_LAT_STEP


async def _fetch_summaries(provider, source_key: str) -> List[Dict[str, Any]]:
    summaries: List[Dict[str, Any]] = []
    page = 1
    max_pages = settings.MAX_PAGES
    logger.info(
        "Fetching up to %d pages from %s (MAX_PAGES=%d)",
        max_pages,
        source_key,
        max_pages,
    )
    while page <= max_pages:
        if hasattr(provider, "search_page"):
            batch, more = await provider.search_page(page=page)
        else:
            batch = await provider.search(bbox=None, page=page)
            more = False
        summaries.extend([_apply_source_fields(item, source_key) for item in batch])
        if not more:
            break
        await asyncio.sleep(1.5)
        page += 1
    return summaries


async def _enrich_summaries(
    provider,
    source_key: str,
    supports_details: bool,
    summaries: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], int]:
    enriched: List[Dict[str, Any]] = []
    detail_calls_made = 0
    max_detail_calls = settings.MAX_DETAIL_CALLS
    limit_logged = False

    if summaries:
        logger.info(
            "Enriching up to %d listings with full details from %s (MAX_DETAIL_CALLS=%d)",
            max_detail_calls,
            source_key,
            max_detail_calls,
        )

    for i, summary_listing in enumerate(summaries):
        listing_id = summary_listing.get("source_listing_id") or summary_listing.get(
            "listing_id"
        )
        logger.debug(
            "Processing listing %d/%d (%s), ID: %s",
            i + 1,
            len(summaries),
            source_key,
            listing_id,
        )

        listing_to_add = summary_listing.copy()
        if not listing_id:
            logger.warning(
                "Skipping enrichment for listing without listing_id (%s): %s",
                source_key,
                summary_listing.get("address"),
            )
            enriched.append(_apply_source_fields(listing_to_add, source_key))
            continue

        if supports_details and detail_calls_made < max_detail_calls:
            try:
                details = await provider.get_details(listing_id)
                detail_calls_made += 1
                await asyncio.sleep(0.5)

                listing_to_add.update(
                    {k: v for k, v in details.items() if v is not None}
                )

                if "photos" in details:
                    listing_to_add["photos"] = details.get("photos") or []
                elif not listing_to_add.get("photos"):
                    listing_to_add["photos"] = []
            except Exception as exc:
                logger.error(
                    "Error fetching details for %s %s: %s",
                    source_key,
                    listing_id,
                    exc,
                    exc_info=True,
                )
        elif (
            supports_details
            and detail_calls_made >= max_detail_calls
            and not limit_logged
        ):
            logger.info(
                "Reached detail call limit (%d) for %s. Skipping remaining details.",
                max_detail_calls,
                source_key,
            )
            limit_logged = True

        description = listing_to_add.get("description") or ""
        listing_to_add["flags"] = extract_flags(description) if description else {}

        lat = listing_to_add.get("lat")
        lon = listing_to_add.get("lon")
        if lat and lon:
            try:
                tranquility = calculate_tranquility_score(lat, lon)
                listing_to_add["tranquility_score"] = tranquility["score"]
                listing_to_add["tranquility_factors"] = tranquility["factors"]
            except Exception as exc:
                logger.debug(
                    "Could not calculate tranquility for %s: %s", listing_id, exc
                )

        neighborhood = listing_to_add.get("neighborhood")
        normalized = resolve_neighborhood(neighborhood, lat, lon)
        if normalized:
            listing_to_add["neighborhood"] = normalized

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
        except Exception as exc:
            logger.debug(
                "Could not calculate light potential for %s: %s", listing_id, exc
            )

        enriched.append(_apply_source_fields(listing_to_add, source_key))

    return enriched, detail_calls_made


async def run_ingestion_job():
    start_time = datetime.now(timezone.utc)
    ingestion_state.last_run_start_time = start_time
    ingestion_state.last_run_end_time = None
    ingestion_state.last_run_summary_count = 0
    ingestion_state.last_run_detail_calls = 0
    ingestion_state.last_run_upsert_count = 0
    ingestion_state.last_run_error = None
    logger.info("Starting ingestion job at %s", start_time.isoformat())

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
                try:
                    provider_summaries = await _fetch_summaries(provider, spec.key)
                    summary_count_total += len(provider_summaries)
                except Exception as exc:
                    logger.error(
                        "Error fetching %s listing summaries: %s",
                        spec.key,
                        exc,
                        exc_info=True,
                    )
                    ingestion_state.last_run_error = (
                        f"Failed during summary fetch ({spec.key}): {exc}"
                    )

                if provider_summaries:
                    provider_enriched, detail_calls_made = await _enrich_summaries(
                        provider,
                        spec.key,
                        spec.supports_details,
                        provider_summaries,
                    )
                    detail_calls_total += detail_calls_made
            finally:
                try:
                    if hasattr(provider, "close"):
                        await provider.close()
                except Exception as exc:
                    logger.error(
                        "Error closing %s provider: %s", spec.key, exc, exc_info=True
                    )

            if provider_enriched:
                upsert_listings(provider_enriched)
                upsert_total += len(provider_enriched)
                all_enriched.extend(provider_enriched)
                logger.info(
                    "Ingestion job upserted %d listings for %s",
                    len(provider_enriched),
                    spec.key,
                )

        ingestion_state.last_run_summary_count = summary_count_total
        ingestion_state.last_run_detail_calls = detail_calls_total
        ingestion_state.last_run_upsert_count = upsert_total

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

    except Exception as exc:
        logger.error("Unhandled error during ingestion job: %s", exc, exc_info=True)
        ingestion_state.last_run_error = f"Unhandled error: {exc}"
    finally:
        end_time = datetime.now(timezone.utc)
        ingestion_state.last_run_end_time = end_time
        duration = (end_time - start_time).total_seconds()
        logger.info(
            "Job finished at %s (Duration: %.2fs)", end_time.isoformat(), duration
        )


def run_ingestion_job_sync():
    """Blocking entry for celery/apscheduler/routes."""
    asyncio.run(run_ingestion_job())
