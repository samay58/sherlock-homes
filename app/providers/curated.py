import logging
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml

from app.core.config import settings
from app.providers.base import BaseProvider
from app.providers.html_parsing import parse_listing_from_html
from app.providers.zenrows_universal import ZenRowsUniversalClient

logger = logging.getLogger(__name__)


class CuratedProvider(BaseProvider):
    """Ingest curated realtor listings from a local YAML file."""

    def __init__(self, path: str | None = None, concurrency: int = 2):
        self.path = Path(path or settings.CURATED_SOURCES_PATH)
        self._client = ZenRowsUniversalClient(concurrency=concurrency)

    async def search(self, bbox=None, page: int = 1) -> Iterable[Dict[str, Any]]:  # type: ignore[override]
        sources = self._load_sources()
        listings: List[Dict[str, Any]] = []
        for source in sources:
            source_name = str(source.get("name") or "curated")
            source_key = f"curated-{_slugify(source_name)}"
            for entry in source.get("listings") or []:
                listing = dict(entry)
                url = listing.get("url")
                source_listing_id = url or listing.get("id") or listing.get("address")
                if not source_listing_id:
                    source_listing_id = f"{source_key}:{len(listings)}"
                listing["source"] = source_key
                listing["source_listing_id"] = str(source_listing_id)
                listings.append(listing)
        logger.info("Curated sources loaded %d listings", len(listings))
        return listings

    async def get_details(self, listing_id: str) -> Dict[str, Any]:
        if not listing_id or not listing_id.startswith("http"):
            return {}
        html = await self._client.fetch(listing_id, js_render=True, premium_proxy=True)
        data = parse_listing_from_html(html)
        data["source_listing_id"] = listing_id
        if not data.get("url"):
            data["url"] = listing_id
        return data

    async def close(self):
        await self._client.close()

    def _load_sources(self) -> List[Dict[str, Any]]:
        if not self.path.exists():
            logger.info("Curated sources file not found: %s", self.path)
            return []
        raw = self.path.read_text(encoding="utf-8")
        payload = yaml.safe_load(raw) or {}
        return payload.get("sources") or []


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned[:24] or "curated"
