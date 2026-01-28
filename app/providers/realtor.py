import logging
import re
from typing import Any, Dict, Iterable, List
from urllib.parse import urlsplit

from app.core.config import settings
from app.providers.base import BaseProvider
from app.providers.html_parsing import (extract_embedded_property_data,
                                        extract_item_list_urls,
                                        merge_listing_fields,
                                        parse_listing_from_html)
from app.providers.zenrows_universal import ZenRowsUniversalClient

logger = logging.getLogger(__name__)

DEFAULT_SEARCH_URL = (
    "https://www.realtor.com/realestateandhomes-search/San-Francisco_CA"
)
LISTING_URL_RE = re.compile(
    r"https?://www\.realtor\.com/realestateandhomes-detail/[^\"'\\s]+"
)


class RealtorProvider(BaseProvider):
    """Fetch Realtor.com listings via ZenRows universal scraping API."""

    def __init__(self, search_url: str | None = None, concurrency: int = 4):
        self.search_url = (
            search_url or settings.REALTOR_SEARCH_URL or DEFAULT_SEARCH_URL
        )
        self._client = ZenRowsUniversalClient(concurrency=concurrency)

    async def search(self, bbox=None, page: int = 1) -> Iterable[Dict[str, Any]]:  # type: ignore[override]
        html = await self._client.fetch(
            self.search_url, js_render=True, premium_proxy=True
        )
        urls = extract_item_list_urls(html)
        if not urls:
            urls = LISTING_URL_RE.findall(html)

        listings: List[Dict[str, Any]] = []
        for url in urls:
            listings.append(
                {
                    "source": "realtor",
                    "source_listing_id": url,
                    "address": _address_from_url(url),
                    "url": url,
                }
            )
        logger.info("Realtor search returned %d candidate listings", len(listings))
        return listings

    async def get_details(self, listing_id: str) -> Dict[str, Any]:
        if not listing_id:
            return {}
        html = await self._client.fetch(listing_id, js_render=True, premium_proxy=True)
        data = parse_listing_from_html(html)
        embedded = extract_embedded_property_data(html)
        data = merge_listing_fields(data, embedded)
        data["source"] = "realtor"
        data["source_listing_id"] = listing_id
        if not data.get("url"):
            data["url"] = listing_id
        return data

    async def close(self):
        await self._client.close()


def _address_from_url(url: str) -> str | None:
    path = urlsplit(url).path.strip("/")
    if not path:
        return None
    segment = path.split("/")[-1]
    if not segment:
        return None
    segment = segment.split("_M")[0]
    segment = segment.replace("_", " ").replace("-", " ").strip()
    return segment or None
