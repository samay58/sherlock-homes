import asyncio
import logging
import re
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.core.config import settings
from app.providers.base import BaseProvider
from app.providers.html_parsing import parse_listing_from_html
from app.providers.zenrows_universal import ZenRowsUniversalClient

logger = logging.getLogger(__name__)

BASE_URL = "https://streeteasy.com"
LISTING_URL_RE = re.compile(
    r"https?://streeteasy\.com/building/[^\"'\s]+/rental/\d+"
)

# Map SE neighborhood slugs to canonical names
SLUG_TO_NEIGHBORHOOD = {
    "williamsburg": "Williamsburg",
    "west-village": "West Village",
    "greenpoint": "Greenpoint",
    "soho": "SoHo",
    "flatiron": "Flatiron",
    "nomad": "NoMad",
    "dumbo": "DUMBO",
    "brooklyn-heights": "Brooklyn Heights",
    "cobble-hill": "Cobble Hill",
    "fort-greene": "Fort Greene",
    "chelsea": "Chelsea",
    "east-village": "East Village",
    "gramercy-park": "Gramercy Park",
    "park-slope": "Park Slope",
    "boerum-hill": "Boerum Hill",
    "clinton-hill": "Clinton Hill",
    "prospect-heights": "Prospect Heights",
    "carroll-gardens": "Carroll Gardens",
    "noho": "NoHo",
    "nolita": "Nolita",
    "lower-east-side": "Lower East Side",
    "greenwich-village": "Greenwich Village",
}


class StreetEasyProvider(BaseProvider):
    """Fetch StreetEasy rental listings via ZenRows universal scraping API."""

    def __init__(self, concurrency: int = 4):
        raw_urls = getattr(settings, "STREETEASY_SEARCH_URLS", "") or ""
        self._search_urls = [u.strip() for u in raw_urls.split(",") if u.strip()]
        self._client = ZenRowsUniversalClient(concurrency=concurrency)

    async def search(self, bbox=None, page: int = 1) -> Iterable[Dict[str, Any]]:  # type: ignore[override]
        """Search a single page across all configured neighborhood URLs."""
        all_listings: List[Dict[str, Any]] = []
        for base_url in self._search_urls:
            try:
                listings = await self._search_neighborhood(base_url, page)
                all_listings.extend(listings)
            except Exception as exc:
                logger.warning(
                    "StreetEasy search failed for %s: %s", base_url, exc
                )
        logger.info(
            "StreetEasy search returned %d candidate listings (page %d)",
            len(all_listings),
            page,
        )
        return all_listings

    async def _search_neighborhood(
        self, base_url: str, page: int = 1
    ) -> List[Dict[str, Any]]:
        url = base_url if page <= 1 else f"{base_url}?page={page}"
        html = await self._client.fetch(
            url,
            js_render=True,
            premium_proxy=True,
            extra_params={"wait_for": ".listingCard,.searchCardList,.listing-row"},
        )

        # Extract neighborhood from URL slug
        neighborhood = _neighborhood_from_url(base_url)

        # Try structured JSON-LD first, then regex for listing URLs
        soup = BeautifulSoup(html, "html.parser")
        urls = LISTING_URL_RE.findall(html)

        # Also look for relative listing links
        for a_tag in soup.select("a[href*='/building/']"):
            href = a_tag.get("href", "")
            if "/rental/" in href:
                full_url = urljoin(BASE_URL, href) if href.startswith("/") else href
                urls.append(full_url)

        # Dedupe
        seen: set[str] = set()
        listings: List[Dict[str, Any]] = []
        for listing_url in urls:
            normalized = listing_url.split("?")[0]  # strip query params
            if normalized in seen:
                continue
            seen.add(normalized)

            # Try to extract minimal info from card HTML near the link
            card_data = _extract_card_data(soup, listing_url)

            listings.append(
                {
                    "source": "streeteasy",
                    "source_listing_id": normalized,
                    "url": normalized,
                    "neighborhood": neighborhood,
                    **card_data,
                }
            )

        return listings

    async def search_page(self, page: int = 1) -> tuple:
        """Multi-page interface used by ingestion.py."""
        items = await self.search(bbox=None, page=page)
        # StreetEasy pagination: assume more pages if we got results
        has_more = len(items) > 0 and page < 5  # cap at 5 pages per neighborhood
        return list(items), has_more

    async def get_details(self, listing_id: str) -> Dict[str, Any]:
        """Fetch and parse a StreetEasy detail page. listing_id is the full URL."""
        if not listing_id:
            return {}
        try:
            html = await self._client.fetch(
                listing_id,
                js_render=True,
                premium_proxy=True,
                extra_params={"wait_for": ".price,.details_info,.BuildingInfo"},
            )
        except Exception as exc:
            logger.warning(
                "StreetEasy detail fetch failed for %s: %s", listing_id, exc
            )
            return {}

        # Try generic JSON-LD parsing first
        data = parse_listing_from_html(html)

        # StreetEasy-specific BS4 parsing to fill gaps
        soup = BeautifulSoup(html, "html.parser")
        _enrich_from_streeteasy_html(soup, data)

        data["source"] = "streeteasy"
        data["source_listing_id"] = listing_id
        if not data.get("url"):
            data["url"] = listing_id

        # Extract neighborhood from URL if not already set
        if not data.get("neighborhood"):
            data["neighborhood"] = _neighborhood_from_url(listing_id)

        return data

    async def close(self):
        await self._client.close()


def _enrich_from_streeteasy_html(soup: BeautifulSoup, data: Dict[str, Any]) -> None:
    """Extract StreetEasy-specific fields from detail page HTML."""

    # Price
    if not data.get("price"):
        price_el = soup.select_one(".price, .details_info_price, [data-testid='price']")
        if price_el:
            data["price"] = _parse_price(price_el.get_text(strip=True))

    # Address
    if not data.get("address"):
        addr_el = soup.select_one(
            ".incognito, .building-title, h1, [data-testid='address']"
        )
        if addr_el:
            data["address"] = addr_el.get_text(strip=True)

    # Beds / Baths / Sqft from detail cells
    if not data.get("beds") or not data.get("baths") or not data.get("sqft"):
        detail_text = " ".join(
            el.get_text(" ", strip=True)
            for el in soup.select(
                ".detail_cell, .details_info .stat, [data-testid='bed-bath-beyond']"
            )
        )
        if not data.get("beds"):
            beds_match = re.search(r"(\d+)\s*(?:bed|br|bedroom)", detail_text, re.I)
            if beds_match:
                data["beds"] = int(beds_match.group(1))
        if not data.get("baths"):
            baths_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:bath|ba)", detail_text, re.I)
            if baths_match:
                data["baths"] = float(baths_match.group(1))
        if not data.get("sqft"):
            sqft_match = re.search(r"([\d,]+)\s*(?:ft|sq)", detail_text, re.I)
            if sqft_match:
                data["sqft"] = int(sqft_match.group(1).replace(",", ""))

    # Days on market
    if not data.get("days_on_market"):
        vitals_text = " ".join(
            el.get_text(" ", strip=True) for el in soup.select(".vitals, .Vitals")
        )
        dom_match = re.search(r"(\d+)\s*days?\s*on\s*StreetEasy", vitals_text, re.I)
        if dom_match:
            data["days_on_market"] = int(dom_match.group(1))

    # Description
    if not data.get("description"):
        desc_el = soup.select_one(
            ".Description-block, .Description, [data-testid='description']"
        )
        if desc_el:
            data["description"] = desc_el.get_text(" ", strip=True)

    # Photos
    if not data.get("photos"):
        photos = []
        for img in soup.select(".gallery img, .Slideshow img, [data-testid='gallery'] img"):
            src = img.get("src") or img.get("data-src")
            if src and src.startswith("http"):
                photos.append(src)
        if not photos:
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                photos.append(str(og_image["content"]))
        if photos:
            data["photos"] = photos

    # Amenities -> boolean flags for scoring
    amenity_text = " ".join(
        el.get_text(" ", strip=True).lower()
        for el in soup.select(".amenities, .AmenitiesList, .BuildingAmenities")
    )
    if amenity_text:
        if "doorman" in amenity_text:
            data.setdefault("has_doorman", True)
        if "elevator" in amenity_text:
            data.setdefault("has_elevator", True)
        if re.search(r"\bgym\b|fitness", amenity_text):
            data.setdefault("has_gym", True)
        if re.search(r"laundry|washer|dryer", amenity_text):
            data.setdefault("has_laundry", True)
        if re.search(r"parking|garage", amenity_text):
            data.setdefault("has_parking", True)
        if re.search(r"dishwasher", amenity_text):
            data.setdefault("has_dishwasher", True)
        if re.search(r"\broof\b|rooftop", amenity_text):
            data.setdefault("has_roof_deck", True)
        if re.search(r"outdoor|patio|terrace|balcony|garden|yard", amenity_text):
            data.setdefault("has_outdoor_space", True)

    # Neighborhood from page
    if not data.get("neighborhood"):
        nbhd_el = soup.select_one(".nobreak, .BuildingInfo-neighborhood")
        if nbhd_el:
            data["neighborhood"] = nbhd_el.get_text(strip=True)


def _extract_card_data(soup: BeautifulSoup, listing_url: str) -> Dict[str, Any]:
    """Try to extract minimal listing data from a search card near the listing link."""
    data: Dict[str, Any] = {}
    # Find the anchor tag for this listing
    link = soup.find("a", href=lambda h: h and listing_url.rstrip("/").endswith(h.rstrip("/").split("streeteasy.com")[-1]) if h else False)
    if not link:
        return data

    # Walk up to find the card container
    card = link.find_parent(class_=re.compile(r"listingCard|listing-row|searchCard"))
    if not card:
        return data

    # Price
    price_el = card.select_one(".price, [data-testid='price']")
    if price_el:
        data["price"] = _parse_price(price_el.get_text(strip=True))

    # Address
    addr_el = card.select_one(".listingCard-title, .details-title, [data-testid='address']")
    if addr_el:
        data["address"] = addr_el.get_text(strip=True)

    return data


def _neighborhood_from_url(url: str) -> Optional[str]:
    """Extract canonical neighborhood name from a StreetEasy URL."""
    match = re.search(r"streeteasy\.com/for-rent/([^/?#]+)", url)
    if not match:
        # Try building URL pattern
        match = re.search(r"streeteasy\.com/building/([^/]+)", url)
    if match:
        slug = match.group(1)
        return SLUG_TO_NEIGHBORHOOD.get(slug, slug.replace("-", " ").title())
    return None


def _parse_price(text: str) -> Optional[float]:
    cleaned = text.replace(",", "").replace("$", "")
    match = re.search(r"\d+(?:\.\d+)?", cleaned)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None
