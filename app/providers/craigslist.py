import logging
import re
from typing import Any, Dict, Iterable, List

from bs4 import BeautifulSoup

from app.core.config import settings
from app.providers.base import BaseProvider
from app.providers.html_parsing import extract_item_list_urls, parse_listing_from_html
from app.providers.zenrows_universal import ZenRowsUniversalClient

logger = logging.getLogger(__name__)

DEFAULT_SEARCH_URL = "https://sfbay.craigslist.org/search/rea"
LISTING_URL_RE = re.compile(r"https?://[\\w.-]*craigslist\\.org/[^\"'\\s]+/\\d+\\.html")


class CraigslistProvider(BaseProvider):
    """Fetch Craigslist real estate listings via ZenRows universal scraping API."""

    def __init__(self, search_url: str | None = None, concurrency: int = 4):
        self.search_url = search_url or settings.CRAIGSLIST_SEARCH_URL or DEFAULT_SEARCH_URL
        self._client = ZenRowsUniversalClient(concurrency=concurrency)

    async def search(self, bbox=None, page: int = 1) -> Iterable[Dict[str, Any]]:  # type: ignore[override]
        html = await self._client.fetch(self.search_url, js_render=False, premium_proxy=True)
        urls = extract_item_list_urls(html)
        if not urls:
            urls = LISTING_URL_RE.findall(html)

        listings: List[Dict[str, Any]] = []
        for url in urls:
            listings.append(
                {
                    "source": "craigslist",
                    "source_listing_id": url,
                    "url": url,
                }
            )
        logger.info("Craigslist search returned %d candidate listings", len(listings))
        return listings

    async def get_details(self, listing_id: str) -> Dict[str, Any]:
        if not listing_id:
            return {}
        html = await self._client.fetch(listing_id, js_render=False, premium_proxy=True)
        data = parse_listing_from_html(html)

        soup = BeautifulSoup(html, "html.parser")
        if data.get("price") is None:
            price_tag = soup.select_one(".price")
            if price_tag:
                data["price"] = _parse_price(price_tag.get_text(strip=True))

        attr_text = " ".join([tag.get_text(" ", strip=True) for tag in soup.select("p.attrgroup span")])
        beds_match = re.search(r"(\\d+)br", attr_text)
        if beds_match and data.get("beds") is None:
            data["beds"] = int(beds_match.group(1))
        sqft_match = re.search(r"(\\d+)ft2", attr_text)
        if sqft_match and data.get("sqft") is None:
            data["sqft"] = int(sqft_match.group(1))

        title = soup.select_one("span#titletextonly")
        if title and not data.get("address"):
            data["address"] = title.get_text(strip=True)

        data["source"] = "craigslist"
        data["source_listing_id"] = listing_id
        if not data.get("url"):
            data["url"] = listing_id
        return data

    async def close(self):
        await self._client.close()


def _parse_price(text: str) -> float | None:
    cleaned = text.replace(",", "")
    match = re.search(r"\\d+(?:\\.\\d+)?", cleaned)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None
