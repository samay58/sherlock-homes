import asyncio
import logging
import os
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

ZENROWS_ENDPOINT = "https://api.zenrows.com/v1/"
API_KEY_ENV = "ZENROWS_API_KEY"


class ZenRowsUniversalClient:
    """Thin async wrapper around the ZenRows universal scraping API."""

    def __init__(self, concurrency: int = 6, timeout: Optional[int] = None, max_retries: int = 2):
        api_key = os.getenv(API_KEY_ENV) or settings.ZENROWS_API_KEY
        if not api_key:
            raise RuntimeError("ZENROWS_API_KEY env var required for ZenRowsUniversalClient")
        self.api_key = api_key
        timeout_seconds = timeout if timeout is not None else settings.ZENROWS_TIMEOUT_SECONDS
        self._client = httpx.AsyncClient(timeout=timeout_seconds)
        self._sem = asyncio.Semaphore(concurrency)
        self._max_retries = max_retries

    async def fetch(
        self,
        url: str,
        *,
        js_render: bool = True,
        premium_proxy: bool = True,
        country: Optional[str] = None,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        params: Dict[str, Any] = {
            "apikey": self.api_key,
            "url": url,
        }
        if js_render:
            params["js_render"] = "true"
        if premium_proxy:
            params["premium_proxy"] = "true"
        if country:
            params["country"] = country
        if extra_params:
            params.update(extra_params)

        attempts = self._max_retries + 1
        for attempt in range(1, attempts + 1):
            try:
                async with self._sem:
                    response = await self._client.get(ZENROWS_ENDPOINT, params=params)
                    response.raise_for_status()
                    return response.text
            except httpx.TimeoutException:
                if attempt >= attempts:
                    raise
                backoff = min(2.0 * attempt, 6.0)
                logger.warning(
                    "ZenRows timeout for %s (attempt %d/%d). Retrying in %.1fs",
                    url,
                    attempt,
                    attempts,
                    backoff,
                )
                await asyncio.sleep(backoff)

    async def close(self) -> None:
        await self._client.aclose()
