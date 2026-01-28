import asyncio
import json
import logging
import re
from typing import Any, Dict, Iterable, List, Tuple
from urllib.parse import urlsplit

import httpx

from app.core.config import settings
from app.providers.base import BaseProvider, BoundingBox
from app.providers.html_parsing import (extract_embedded_property_data,
                                        extract_item_list_urls,
                                        merge_listing_fields,
                                        parse_listing_from_html)
from app.providers.zenrows_universal import ZenRowsUniversalClient

logger = logging.getLogger(__name__)


class RedfinProvider(BaseProvider):
    """Fetch listings via Redfin's internal JSON endpoints.

    This first pass only grabs search results; detail fetch implemented later.
    """

    BASE_SEARCH = "https://www.redfin.com/stingray/api/gis"
    BASE_DETAIL = "https://www.redfin.com/stingray/api/home/details"

    def __init__(self, market: str = "sanfrancisco", concurrency: int = 8):
        self.market = market
        self._client = httpx.AsyncClient(headers={"user-agent": "Mozilla/5.0"})
        self._sem = asyncio.Semaphore(concurrency)
        self.search_url = settings.REDFIN_SEARCH_URL
        self._zen_client: ZenRowsUniversalClient | None = None
        self._listing_urls: Dict[str, str] = {}

    async def _fetch(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        async with self._sem:
            r = await self._client.get(url, params=params, timeout=15)
            r.raise_for_status()
            text = r.text
            if text.startswith("{}&&"):
                text = text.split("&&", 1)[1]
            return json.loads(text)

    async def search(
        self, bbox: BoundingBox | None = None, page: int = 1
    ) -> Iterable[Dict[str, Any]]:  # noqa: D401
        self._listing_urls.clear()
        try:
            params = _build_search_params(self.market, bbox, page)
            data = await self._fetch(self.BASE_SEARCH, params)
            homes = data.get("homes", [])
            listings = [
                listing
                for listing in (_normalize_redfin_item(item) for item in homes)
                if listing
            ]
            if listings:
                for listing in listings:
                    if listing.get("source_listing_id") and listing.get("url"):
                        self._listing_urls[str(listing["source_listing_id"])] = listing[
                            "url"
                        ]
                return listings
            logger.info(
                "Redfin direct search returned no listings; falling back to ZenRows"
            )
        except Exception as exc:
            logger.warning(
                "Redfin direct search failed; falling back to ZenRows: %s", exc
            )
        return await self._search_via_zenrows()

    async def get_details(self, listing_id: str) -> Dict[str, Any]:
        if not listing_id:
            return {}
        if listing_id.startswith("http"):
            return await self._details_from_url(listing_id)
        try:
            params = {"propertyId": listing_id, "market": self.market}
            data = await self._fetch(self.BASE_DETAIL, params)
            payload = data.get("payload", {})
            normalized = _normalize_redfin_detail(payload)
            if normalized:
                return normalized
        except Exception as exc:
            logger.warning("Redfin detail fetch failed for %s: %s", listing_id, exc)
        url = self._listing_urls.get(listing_id)
        if url:
            return await self._details_from_url(url)
        return {}

    async def close(self):
        await self._client.aclose()
        if self._zen_client:
            await self._zen_client.close()

    async def _search_via_zenrows(self) -> List[Dict[str, Any]]:
        client = self._ensure_zen_client()
        try:
            html = await client.fetch(
                self.search_url, js_render=True, premium_proxy=True
            )
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code if exc.response else None
            if status == 422:
                logger.warning(
                    "Redfin ZenRows search returned 422; retrying without premium proxy"
                )
                try:
                    html = await client.fetch(
                        self.search_url, js_render=True, premium_proxy=False
                    )
                except httpx.HTTPStatusError as retry_exc:
                    logger.warning(
                        "Redfin ZenRows fallback failed: %s",
                        retry_exc,
                    )
                    return []
            else:
                logger.warning("Redfin ZenRows search failed: %s", exc)
                return []
        urls = extract_item_list_urls(html)
        if not urls:
            urls = REDFIN_LISTING_URL_RE.findall(html)
        if not urls:
            urls = REDFIN_RELATIVE_URL_RE.findall(html)

        listings: List[Dict[str, Any]] = []
        for url in urls:
            normalized_url = _normalize_url(url)
            listings.append(
                {
                    "source": "redfin",
                    "source_listing_id": normalized_url,
                    "url": normalized_url,
                    "address": _address_from_url(normalized_url),
                }
            )
        logger.info(
            "Redfin ZenRows search returned %d candidate listings", len(listings)
        )
        return listings

    async def _details_from_url(self, url: str) -> Dict[str, Any]:
        client = self._ensure_zen_client()
        html = await client.fetch(url, js_render=True, premium_proxy=True)
        data = parse_listing_from_html(html)
        embedded = extract_embedded_property_data(html)
        data = merge_listing_fields(data, embedded)
        data["source"] = "redfin"
        data["source_listing_id"] = url
        if not data.get("url"):
            data["url"] = url
        return data

    def _ensure_zen_client(self) -> ZenRowsUniversalClient:
        if self._zen_client is None:
            self._zen_client = ZenRowsUniversalClient(concurrency=4)
        return self._zen_client


REDFIN_LISTING_URL_RE = re.compile(r"https?://www\.redfin\.com/[^\s\"']+/home/\d+")
REDFIN_RELATIVE_URL_RE = re.compile(r"/[^\s\"']+/home/\d+")


def _build_search_params(
    market: str, bbox: BoundingBox | None, page: int
) -> Dict[str, Any]:
    if bbox:
        lat_lo, lon_lo, lat_hi, lon_hi = bbox
        return {
            "al": 1,
            "market": market,
            "num_homes": 350,
            "ord": "redfin-recommended-asc",
            "status": 9,
            "uipt": "1,2,3,4,5,6",
            "v": 8,
            "lat": f"{lat_lo},{lat_hi}",
            "long": f"{lon_lo},{lon_hi}",
            "page_number": page,
        }
    return {
        "al": 1,
        "market": market,
        "num_homes": 350,
        "ord": "redfin-recommended-asc",
        "status": 9,
        "uipt": "1,2,3,4,5,6",
        "v": 8,
        "location": "San Francisco, CA",
        "page_number": page,
    }


def _normalize_redfin_item(item: Dict[str, Any]) -> Dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    url = item.get("url") or item.get("listingUrl") or item.get("urlV2")
    if isinstance(url, str) and url.startswith("/"):
        url = f"https://www.redfin.com{url}"

    street = item.get("streetLine") or item.get("address") or item.get("streetAddress")
    address = (
        _format_address(
            street,
            item.get("city"),
            item.get("state"),
            item.get("zip") or item.get("zipCode"),
        )
        or street
    )

    source_listing_id = item.get("propertyId") or item.get("listingId") or url
    if not source_listing_id or not address:
        return None

    photo = item.get("photoUrl") or item.get("photo_url") or item.get("imageUrl")
    photos = [photo] if isinstance(photo, str) else []

    return {
        "source": "redfin",
        "source_listing_id": str(source_listing_id),
        "address": address,
        "price": item.get("price") or item.get("listPrice"),
        "beds": item.get("beds") or item.get("bedrooms"),
        "baths": item.get("baths") or item.get("bathrooms"),
        "sqft": item.get("sqft") or item.get("sqFt") or item.get("livingArea"),
        "lat": item.get("lat") or item.get("latitude"),
        "lon": item.get("lng") or item.get("longitude"),
        "url": url,
        "listing_status": item.get("status"),
        "property_type": item.get("propertyType"),
        "photos": photos,
    }


def _normalize_redfin_detail(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not payload:
        return {}
    address = payload.get("address")
    if isinstance(address, dict):
        address = _format_address(
            address.get("streetLine"),
            address.get("city"),
            address.get("state"),
            address.get("zip"),
        )
    return {
        "description": payload.get("remarks") or payload.get("description"),
        "price": payload.get("price"),
        "beds": payload.get("beds") or payload.get("bedrooms"),
        "baths": payload.get("baths") or payload.get("bathrooms"),
        "sqft": payload.get("sqft") or payload.get("livingArea"),
        "lat": payload.get("lat") or payload.get("latitude"),
        "lon": payload.get("lng") or payload.get("longitude"),
        "address": address,
        "photos": _extract_photo_urls(payload.get("photos")),
        "year_built": payload.get("yearBuilt"),
    }


def _format_address(street: Any, city: Any, state: Any, zip_code: Any) -> str | None:
    parts = [str(part).strip() for part in [street, city, state, zip_code] if part]
    return ", ".join(parts) if parts else None


def _extract_photo_urls(value: Any) -> List[str]:
    urls: List[str] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                urls.append(item)
            elif isinstance(item, dict):
                url = item.get("url") or item.get("href")
                if isinstance(url, str):
                    urls.append(url)
    return urls


def _normalize_url(url: str) -> str:
    if url.startswith("/"):
        return f"https://www.redfin.com{url}"
    return url


def _address_from_url(url: str) -> str | None:
    path = urlsplit(url).path.strip("/")
    if not path:
        return None
    parts = path.split("/")
    if "home" in parts:
        idx = parts.index("home")
        segment = parts[idx - 1] if idx > 0 else parts[-1]
    else:
        segment = parts[-1]
    segment = segment.split("_")[0]
    segment = segment.replace("-", " ").strip()
    return segment or None
