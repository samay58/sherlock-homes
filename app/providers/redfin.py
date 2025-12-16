import asyncio
import logging
from typing import Dict, Any, Iterable, List, Tuple

import httpx
import json

from .base import BaseProvider, BoundingBox

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

    async def _fetch(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        async with self._sem:
            r = await self._client.get(url, params=params, timeout=15)
            r.raise_for_status()
            text = r.text
            if text.startswith("{}&&"):
                text = text.split("&&", 1)[1]
            return json.loads(text)

    async def search(self, bbox: BoundingBox | None = None, page: int = 1) -> Iterable[Dict[str, Any]]:  # noqa: D401
        # If bbox provided, attempt; else fall back to location param (more reliable)
        if bbox:
            lat_lo, lon_lo, lat_hi, lon_hi = bbox
            params = {
                "al": 1,
                "market": self.market,
                "num_homes": 350,
                "ord": "redfin-recommended-asc",
                "status": 9,
                "uipt": "1,2,3,4,5,6",
                "v": 8,
                "lat": f"{lat_lo},{lat_hi}",
                "long": f"{lon_lo},{lon_hi}",
                "page_number": page,
            }
        else:
            params = {
                "al": 1,
                "market": self.market,
                "num_homes": 350,
                "ord": "redfin-recommended-asc",
                "status": 9,
                "uipt": "1,2,3,4,5,6",
                "v": 8,
                "location": "San Francisco, CA",
                "page_number": page,
            }
        data = await self._fetch(self.BASE_SEARCH, params)
        return data.get("homes", [])

    async def get_details(self, listing_id: str) -> Dict[str, Any]:
        params = {"propertyId": listing_id, "market": self.market}
        data = await self._fetch(self.BASE_DETAIL, params)
        return data.get("payload", {})

    async def close(self):
        await self._client.aclose() 