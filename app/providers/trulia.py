import logging
import re
from typing import Any, Dict, Iterable, List
from urllib.parse import urljoin, urlsplit

import httpx

from app.core.config import settings
from app.providers.base import BaseProvider
from app.providers.html_parsing import (extract_embedded_property_data,
                                        extract_item_list_urls,
                                        merge_listing_fields,
                                        parse_listing_from_html)
from app.providers.zenrows_universal import ZenRowsUniversalClient

logger = logging.getLogger(__name__)

DEFAULT_SEARCH_URL = "https://www.trulia.com/for_sale/San_Francisco,CA/"
BASE_URL = "https://www.trulia.com"
LISTING_URL_RE = re.compile(r"https?://www\.trulia\.com/(?:p|home)/[^\"'\\s]+")


class TruliaProvider(BaseProvider):
    """Fetch Trulia listings via ZenRows universal scraping API."""

    def __init__(self, search_url: str | None = None, concurrency: int = 4):
        self.search_url = search_url or settings.TRULIA_SEARCH_URL or DEFAULT_SEARCH_URL
        self._client = ZenRowsUniversalClient(concurrency=concurrency)

    async def search(self, bbox=None, page: int = 1) -> Iterable[Dict[str, Any]]:  # type: ignore[override]
        html = await self._client.fetch(
            self.search_url, js_render=True, premium_proxy=True
        )
        urls = extract_item_list_urls(html)
        urls.extend(LISTING_URL_RE.findall(html))
        normalized_urls: List[str] = []
        seen = set()
        for url in urls:
            normalized = _normalize_trulia_url(url)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            normalized_urls.append(normalized)

        listings: List[Dict[str, Any]] = []
        for url in normalized_urls:
            listings.append(
                {
                    "source": "trulia",
                    "source_listing_id": url,
                    "address": _address_from_url(url),
                    "url": url,
                }
            )
        logger.info("Trulia search returned %d candidate listings", len(listings))
        return listings

    async def get_details(self, listing_id: str) -> Dict[str, Any]:
        if not listing_id:
            return {}
        if not _looks_complete_trulia_url(listing_id):
            logger.debug("Skipping Trulia details for incomplete URL: %s", listing_id)
            return {}
        try:
            html = await self._client.fetch(
                listing_id, js_render=True, premium_proxy=True
            )
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code if exc.response else None
            if status in {404, 410}:
                logger.info(
                    "Trulia listing unavailable (%s). Skipping: %s", status, listing_id
                )
                return {}
            raise
        data = parse_listing_from_html(html)
        embedded = extract_embedded_property_data(html)
        data = merge_listing_fields(data, embedded)
        data["source"] = "trulia"
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
    segment = segment.split("--")[0]
    segment = segment.replace("-", " ").replace("_", " ").strip()
    return segment or None


def _normalize_trulia_url(url: str) -> str | None:
    if not url:
        return None
    if url.startswith("/"):
        return urljoin(BASE_URL, url)
    return url


def _looks_complete_trulia_url(url: str) -> bool:
    path = urlsplit(url).path.strip("/")
    if not path:
        return False
    # Typical Trulia listings include an id suffix (either /<digits> or --<digits>).
    return bool(re.search(r"/\d+$", path) or re.search(r"--\d+$", path))
