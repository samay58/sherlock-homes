import asyncio
import logging
import os
import re
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.listing import PropertyListing
from app.services.nlp import extract_flags
from app.services.persistence import upsert_listings

logger = logging.getLogger(__name__)

CITY_SLUG = "San-Francisco"
BASE = f"https://www.redfin.com/city/17151/CA/{CITY_SLUG}"
RESULT_PATH = "/filter/include=sold-6mo"

CONCURRENCY = 8
HEADERS = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
}

# verify env vars for WalkScore before attempting
walk_env_ok = all(
    env in os.environ for env in ("WALKSCORE_API_KEY", "WALKSCORE_HOST")
)


# ------------------ helper utils ------------------


def _parse_num(raw: Optional[str]) -> Optional[float]:
    """Grab first numeric token from a string (commas removed)."""
    if not raw:
        return None
    match = re.search(r"[\d,.]+", raw)
    if not match:
        return None
    return float(match.group().replace(",", ""))


def _normalize_photo(url: str) -> str:
    """Strip size/transform segments to get stable path."""
    parts = PurePosixPath(url).parts
    try:
        idx = parts.index("photos")
        return "/".join(parts[: idx + 2]) + ".jpg"
    except ValueError:
        return url


async def _walk_score(client: httpx.AsyncClient, address: str, lat: float, lon: float) -> Optional[int]:
    if not walk_env_ok:
        return None
    try:
        r = await client.get(
            os.environ["WALKSCORE_HOST"],
            params={
                "format": "json",
                "address": address,
                "lat": lat,
                "lon": lon,
                "wsapikey": os.environ["WALKSCORE_API_KEY"],
            },
            timeout=10,
        )
        r.raise_for_status()
        return int(r.json().get("walkscore", 0))
    except Exception as exc:  # noqa: BLE001
        logger.debug("walkscore fail %s", exc)
        return None


# ------------------ core scraping ------------------


async def _scrape_listing(client: httpx.AsyncClient, url: str) -> Optional[Dict[str, Any]]:
    try:
        res = await client.get(url, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        def sel(text: str) -> Optional[str]:
            node = soup.select_one(text)
            return node.get_text(" ", strip=True) if node else None

        address = sel("span.street-address") or sel("h1.address")
        price = _parse_num(sel("div.home-main-stats span"))
        beds_raw = _parse_num(sel("div.stats li:nth-child(1)"))
        beds = int(beds_raw) if beds_raw is not None else None
        baths = _parse_num(sel("div.stats li:nth-child(2)"))
        sqft_raw = _parse_num(sel("div.stats li:nth-child(3)"))
        sqft = int(sqft_raw) if sqft_raw is not None else None
        property_type = sel("div.keyDetail:contains('Property Type') span.value")
        dom = _parse_num(sel("div.keyDetail:contains('Days on Market') span.value"))
        description = sel("div.remarks-section") or sel("div#marketing-description")
        photos = [
            _normalize_photo(img["src"])
            for img in soup.select("img.PhotoSliderImage")
            if img.get("src")
        ][:10]

        flags = extract_flags(description or "")

        coord_match = re.search(r'"latitude":([\d.]+),"longitude":([\d.]+)', res.text)
        lat, lon = (float(coord_match.group(1)), float(coord_match.group(2))) if coord_match else (None, None)
        walk = await _walk_score(client, address, lat, lon) if lat and lon else None

        return {
            "address": address,
            "price": price,
            "beds": beds,
            "baths": baths,
            "sqft": sqft,
            "property_type": property_type,
            "url": url,
            "description": description,
            "days_on_market": dom,
            "flags": flags,
            "photos": photos,
            "walk_score": walk,
        }
    except Exception as exc:  # noqa: BLE001
        logger.debug("listing scrape failed %s: %s", url, exc)
        return None


async def _crawl_pages() -> List[Dict[str, Any]]:
    """Iterate result pages and gather listing data."""
    listings: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(headers=HEADERS) as client:
        next_url: Optional[str] = BASE + RESULT_PATH
        page_no = 1
        while next_url:
            logger.info("Scraping search page %d", page_no)
            resp = await client.get(next_url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            card_links = {
                "https://www.redfin.com" + a["href"]
                for a in soup.select("div.HomeCardContainer a.cover-all-link")
                if a.get("href")
            }

            sem = asyncio.Semaphore(CONCURRENCY)

            async def throttle(u: str):
                async with sem:
                    return await _scrape_listing(client, u)

            page_data = await asyncio.gather(*[throttle(u) for u in card_links])
            listings.extend([d for d in page_data if d])

            nxt = soup.select_one("a.PagedResultsButton-sectionRight")
            next_url = "https://www.redfin.com" + nxt["href"] if nxt else None
            page_no += 1
    return listings


# ------------------ persistence ------------------


def _upsert(listings: List[Dict[str, Any]]):
    # Backwards-compatible shim; prefer `upsert_listings`
    upsert_listings(listings)


# ------------------ public API ------------------


def run_scrape_job() -> None:
    """Entry point wired to APScheduler and admin endpoint."""
    logger.info("Starting Redfin scrape job…")
    items = asyncio.run(_crawl_pages())
    logger.info("%d listings fetched", len(items))
    upsert_listings(items)
    logger.info("Scraping complete.")


def scraper_status(db: Session) -> Dict[str, Any]:
    return {"timestamp": datetime.utcnow().isoformat(), "listings": db.query(PropertyListing).count()} 
