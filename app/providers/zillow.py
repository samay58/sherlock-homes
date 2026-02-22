import asyncio
import json
import logging
import os
import urllib.parse
from typing import Any, Dict, Iterable, List, Optional

import httpx

from app.core.config import settings

from .base import BaseProvider

# from bs4 import BeautifulSoup # No longer needed if we only parse JSON


logger = logging.getLogger(__name__)

ZENROWS_ENDPOINT = "https://api.zenrows.com/v1/"
REAL_ESTATE_DISCOVERY_ENDPOINT = "https://realestate.api.zenrows.com/v1/targets/zillow/discovery/"  # Renamed for clarity
ZILLOW_PROPERTY_DETAIL_ENDPOINT = (
    "https://realestate.api.zenrows.com/v1/targets/zillow/properties/"  # New endpoint
)
API_KEY_ENV = "ZENROWS_API_KEY"
DEFAULT_LOCATION = "san-francisco-ca"

# Map Zillow location slugs to canonical neighborhood names
SLUG_TO_NEIGHBORHOOD = {
    "williamsburg-brooklyn-new-york-ny": "Williamsburg",
    "north-williamsburg-brooklyn-new-york-ny": "North Williamsburg",
    "south-williamsburg-brooklyn-new-york-ny": "South Williamsburg",
    "east-williamsburg-brooklyn-new-york-ny": "East Williamsburg",
    "greenpoint-brooklyn-new-york-ny": "Greenpoint",
    "dumbo-brooklyn-new-york-ny": "DUMBO",
    "brooklyn-heights-brooklyn-new-york-ny": "Brooklyn Heights",
    "cobble-hill-brooklyn-new-york-ny": "Cobble Hill",
    "boerum-hill-brooklyn-new-york-ny": "Boerum Hill",
    "carroll-gardens-brooklyn-new-york-ny": "Carroll Gardens",
    "fort-greene-brooklyn-new-york-ny": "Fort Greene",
    "clinton-hill-brooklyn-new-york-ny": "Clinton Hill",
    "park-slope-brooklyn-new-york-ny": "Park Slope",
    "prospect-heights-brooklyn-new-york-ny": "Prospect Heights",
    "west-village-new-york-ny": "West Village",
    "greenwich-village-new-york-ny": "Greenwich Village",
    "soho-new-york-ny": "SoHo",
    "noho-new-york-ny": "NoHo",
    "nolita-new-york-ny": "Nolita",
    "flatiron-new-york-ny": "Flatiron",
    "nomad-new-york-ny": "NoMad",
    "gramercy-park-new-york-ny": "Gramercy Park",
    "gramercy-new-york-ny": "Gramercy",
    "chelsea-new-york-ny": "Chelsea",
    "east-village-new-york-ny": "East Village",
    "lower-east-side-new-york-ny": "Lower East Side",
}


class ZillowProvider(BaseProvider):
    """Fetch Zillow search results via ZenRows anti-bot service."""

    def __init__(
        self,
        location_slug: Optional[str] = None,
        concurrency: int = 6,
        price_min: Optional[int] = None,
        price_max: Optional[int] = None,
        beds_min: Optional[int] = None,
        baths_min: Optional[float] = None,
        sqft_min: Optional[int] = None,
        property_types: Optional[List[str]] = None,
    ):
        api_key = os.getenv(API_KEY_ENV) or settings.ZENROWS_API_KEY
        if not api_key:
            raise RuntimeError("ZENROWS_API_KEY env var required for ZillowProvider")

        self.api_key = api_key
        # Support multi-neighborhood search via SEARCH_LOCATIONS (comma-separated)
        if location_slug is not None:
            self.location_slugs = [location_slug]
        elif getattr(settings, "SEARCH_LOCATIONS", ""):
            self.location_slugs = [
                s.strip() for s in settings.SEARCH_LOCATIONS.split(",") if s.strip()
            ]
        else:
            self.location_slugs = [settings.SEARCH_LOCATION]
        self.location_slug = self.location_slugs[0]  # default for single-location calls
        # Use settings defaults if not provided
        self.price_min = (
            price_min if price_min is not None else settings.SEARCH_PRICE_MIN
        )
        self.price_max = (
            price_max if price_max is not None else settings.SEARCH_PRICE_MAX
        )
        self.beds_min = beds_min if beds_min is not None else settings.SEARCH_BEDS_MIN
        self.baths_min = (
            baths_min if baths_min is not None else settings.SEARCH_BATHS_MIN
        )
        self.sqft_min = sqft_min if sqft_min is not None else settings.SEARCH_SQFT_MIN
        self.search_mode = getattr(settings, "SEARCH_MODE", "buy").lower()
        if self.search_mode == "rent":
            self.property_types = property_types or ["apartment", "condo", "townhouse"]
        else:
            self.property_types = property_types or ["single-family", "condo", "townhouse"]
        self.client = httpx.AsyncClient(timeout=settings.ZENROWS_TIMEOUT_SECONDS)
        self.sem = asyncio.Semaphore(concurrency)

        # Log the configured search parameters
        logger.info(
            f"ZillowProvider initialized for location='{self.location_slug}' with filters: "
            f"price_min={self.price_min}, price_max={self.price_max}, beds_min={self.beds_min}, "
            f"baths_min={self.baths_min}, sqft_min={self.sqft_min}"
        )

    async def _zenrows_get(
        self, endpoint: str, params: Dict[str, Any], label: str
    ) -> str:
        attempts = 3
        for attempt in range(1, attempts + 1):
            try:
                async with self.sem:
                    r = await self.client.get(endpoint, params=params)
                    r.raise_for_status()
                    return r.text
            except httpx.TimeoutException:
                if attempt >= attempts:
                    raise
                backoff = min(2.0 * attempt, 6.0)
                logger.warning(
                    "Zillow %s request timed out (attempt %d/%d). Retrying in %.1fs",
                    label,
                    attempt,
                    attempts,
                    backoff,
                )
                await asyncio.sleep(backoff)

        raise RuntimeError(f"Zillow {label} request failed after retries")

    async def _zenrows_get_discovery(self, url: str) -> str:  # Renamed for clarity
        """Call ZenRows Zillow discovery endpoint which returns structured JSON."""
        params = {
            "apikey": self.api_key,
            "url": url,
        }
        # Use REAL_ESTATE_DISCOVERY_ENDPOINT here
        return await self._zenrows_get(
            REAL_ESTATE_DISCOVERY_ENDPOINT, params, "discovery"
        )

    async def _zenrows_get_property_details(self, zpid: str) -> str:
        """Call ZenRows Zillow property detail endpoint for a given ZPID."""
        detail_url = f"{ZILLOW_PROPERTY_DETAIL_ENDPOINT}{zpid}"
        params = {
            "apikey": self.api_key,
            "country": "us",  # Optional parameter added back based on docs example
        }
        logger.debug(
            "Making HTTP GET request to ZenRows Property Detail API for ZPID: %s at URL: %s",
            zpid,
            detail_url,
        )
        return await self._zenrows_get(detail_url, params, "detail")

    def _build_search_url(self, page: int = 1, keyword: Optional[str] = None) -> str:
        base = f"https://www.zillow.com/{self.location_slug}/"

        # Add rental path segment if in rent mode
        if self.search_mode == "rent":
            base += "rentals/"

        # Build dynamic filters based on initialized parameters
        filters = []

        # Beds filter
        if self.beds_min:
            filters.append(f"{self.beds_min}-_beds")

        # Baths filter
        if self.baths_min:
            filters.append(f"{self.baths_min}-_baths")

        # Size filter
        if self.sqft_min:
            filters.append(f"{self.sqft_min}-_size")

        # Price range filter
        if self.price_min and self.price_max:
            filters.append(f"{self.price_min}-{self.price_max}_price")
        elif self.price_min:
            filters.append(f"{self.price_min}_price")  # Open-ended upper bound
        elif self.price_max:
            filters.append(f"0-{self.price_max}_price")

        # Add filters to URL
        if filters:
            base += "/".join(filters) + "/"

        # Add property type filters if specific types requested
        # Note: Zillow URL structure for property types may vary
        # This is a simplified approach

        parts = []
        if keyword:
            parts.append(urllib.parse.quote_plus(keyword))
        if page > 1:
            parts.append(f"{page}_p/")

        return base + "".join(parts)

    async def search(self, bbox=None, page: int = 1, keyword: Optional[str] = None) -> Iterable[Dict[str, Any]]:  # type: ignore[override]
        url = self._build_search_url(page=page, keyword=keyword)
        raw = await self._zenrows_get_discovery(url)  # Use renamed helper
        try:
            js = json.loads(raw)
            list_results = js.get("property_list", [])
            self._next_exists = bool(js.get("pagination", {}).get("next_page"))
        except Exception as exc:
            logger.debug("Bad JSON from ZenRows: %s", exc)
            return []

        # Resolve canonical neighborhood from the search slug
        search_neighborhood = SLUG_TO_NEIGHBORHOOD.get(self.location_slug)

        items: List[Dict[str, Any]] = []
        for res in list_results:
            price = res.get("property_price") or res.get("price")
            identifier = res.get("property_id") or res.get("zpid")
            if not identifier:
                continue
            # Use the search-slug neighborhood if the API only returns a generic borough
            raw_neighborhood = res.get("neighborhood") or res.get("city")
            if search_neighborhood and (
                not raw_neighborhood
                or raw_neighborhood.lower() in ("brooklyn", "new york", "manhattan", "queens")
            ):
                raw_neighborhood = search_neighborhood

            items.append(
                {
                    "source": "zillow",
                    "source_listing_id": str(identifier),
                    "listing_id": str(identifier),
                    "address": res.get("property_address"),
                    "lat": res.get("latitude"),
                    "lon": res.get("longitude"),
                    "price": price,
                    "beds": res.get("bedrooms_count"),
                    "baths": res.get("bathrooms_count"),
                    "sqft": res.get("property_dimensions"),
                    "url": res.get("property_url"),
                    "listing_status": res.get("property_status"),
                    "property_type": res.get("property_type"),
                    "neighborhood": raw_neighborhood,
                    "flags": {},
                    "photos": (
                        [res.get("property_image")] if res.get("property_image") else []
                    ),
                }
            )
        return items

    async def get_details(self, listing_id: str) -> Dict[str, Any]:
        """Fetch additional details for a listing given its ZPID (listing_id)."""
        if not listing_id:
            logger.warning("No listing_id (ZPID) provided to get_details.")
            return {}
        try:
            raw_details = await self._zenrows_get_property_details(listing_id)
            logger.debug(
                f"<<< Raw Response for ZPID {listing_id}: {raw_details[:500]}... (truncated)"
            )
            details_json = json.loads(raw_details)

            # Extract the fields we care about for enrichment
            description = details_json.get("property_description")
            year_built = details_json.get("year_built")

            # The property API might return a list of photo URLs directly,
            # or under a key like 'property_images' or 'photos'.
            # We need to check common patterns or assume one from the example.
            # The example shows "property_image" (singular) for one main image.
            # Let's assume the detail endpoint might offer more under a "photos" key or similar
            # For now, let's stick to the main one if 'photos' isn't obvious
            # or if we want to keep it simple and aligned with current `photos` field (list of strings)

            photos_list = []
            # Example from docs: "property_image": "url" (singular)
            # If there's a more comprehensive list, e.g. details_json.get("photos_list_key")
            # we would use that. For now, let's assume we are primarily after description and year_built
            # and will keep the single photo logic from search() unless a richer list is found.
            # Let's assume the property detail response might have a 'property_images' list based on Idealista example
            # or just a single 'property_image'. We'll prefer a list if available.

            # According to Zenrows Zillow Property API example, it is "property_image" (singular)
            # but also mentions "Property description and images" (plural) in features.
            # The response example ONLY shows "property_image".
            # Let's be safe and check for a potential list, but fall back to the single image.
            raw_photos = details_json.get("property_images")  # Check for a list
            if isinstance(raw_photos, list):
                photos_list = [str(p) for p in raw_photos if isinstance(p, str)]
            elif details_json.get("property_image"):  # Fallback to single image
                photos_list = [str(details_json["property_image"])]

            # Extract lat/lon for geospatial intelligence
            latitude = details_json.get("latitude")
            longitude = details_json.get("longitude")

            # Extract listing freshness
            listing_days = details_json.get("listing_days")  # How many days on market
            neighborhood = details_json.get("neighborhood") or details_json.get("city")

            return {
                "source": "zillow",
                "source_listing_id": str(listing_id),
                "description": description,
                "year_built": year_built,
                "lat": latitude,
                "lon": longitude,
                "days_on_market": listing_days,
                "neighborhood": neighborhood,
                "photos": (
                    photos_list if photos_list else None
                ),  # Ensure it's None if empty, not [] for consistency
            }
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Failed to get details for ZPID {listing_id}: HTTP {exc.response.status_code}"
            )
            return {}
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON details for ZPID {listing_id}")
            return {}
        except Exception as exc:
            logger.error(f"Error in get_details for ZPID {listing_id}: {exc}")
            return {}

    async def close(self):
        await self.client.aclose()

    async def search_all_locations(self) -> List[Dict[str, Any]]:
        """Search across all configured location slugs, returning combined results."""
        all_items: List[Dict[str, Any]] = []
        for slug in self.location_slugs:
            self.location_slug = slug
            page = 1
            max_pages = 5  # cap per neighborhood to avoid API abuse
            while page <= max_pages:
                items = await self.search(None, page)
                all_items.extend(items)
                has_more = getattr(self, "_next_exists", False)
                if not has_more or not items:
                    break
                page += 1
                await asyncio.sleep(1.5)
            logger.info("Fetched %d items from %s (%d pages)", len(all_items), slug, page)
        return all_items

    async def search_page(self, page: int = 1, keyword: Optional[str] = None):
        # For multi-location, use search_all_locations instead
        if len(self.location_slugs) > 1 and page == 1:
            items = await self.search_all_locations()
            return items, False  # All done in one call

        items = await self.search(None, page, keyword)
        return items, getattr(self, "_next_exists", False)
