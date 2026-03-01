import asyncio
import logging
import re
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from app.core.config import settings
from app.providers.base import BaseProvider
from app.providers.html_parsing import extract_item_list_urls, parse_listing_from_html
from app.providers.zenrows_universal import ZenRowsUniversalClient

logger = logging.getLogger(__name__)

BASE_URL = "https://streeteasy.com"
LISTING_URL_RE = re.compile(
    r"https?://streeteasy\.com/building/[^\"'\s]+/[^\"'\s]+"
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
        self._client = ZenRowsUniversalClient(concurrency=concurrency, timeout=90)

    async def search(self, bbox=None, page: int = 1) -> Iterable[Dict[str, Any]]:  # type: ignore[override]
        """Search a single page across all configured neighborhood URLs."""
        if not self._search_urls:
            logger.info("StreetEasy search skipped: STREETEASY_SEARCH_URLS is empty")
            return []
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
        url = _with_search_filters(base_url, page)
        html = await self._client.fetch(
            url,
            js_render=True,
            premium_proxy=True,
        )

        # Extract neighborhood from URL slug
        neighborhood = _neighborhood_from_url(base_url)

        # Try structured JSON-LD first, then regex + DOM anchors.
        soup = BeautifulSoup(html, "html.parser")
        urls = extract_item_list_urls(html)
        urls.extend(LISTING_URL_RE.findall(html))

        # Also look for relative listing links
        for a_tag in soup.select("a[href*='/building/']"):
            href = a_tag.get("href", "")
            full_url = urljoin(BASE_URL, href) if href.startswith("/") else href
            urls.append(full_url)

        # Dedupe
        seen: set[str] = set()
        listings: List[Dict[str, Any]] = []
        for listing_url in urls:
            normalized = _normalize_streeteasy_url(listing_url)
            if not normalized:
                continue
            if normalized in seen:
                continue
            seen.add(normalized)

            # Try to extract minimal info from card HTML near the link
            card_data = _extract_card_data(soup, normalized)

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

    async def search_all_locations(self) -> List[Dict[str, Any]]:
        """Search all neighborhoods independently, paginating each one fully."""
        if not self._search_urls:
            logger.info("StreetEasy search skipped: STREETEASY_SEARCH_URLS is empty")
            return []

        max_pages = max(1, min(settings.MAX_PAGES, settings.STREETEASY_MAX_PAGES))
        all_listings: List[Dict[str, Any]] = []
        seen_urls: set[str] = set()

        for base_url in self._search_urls:
            neighborhood = _neighborhood_from_url(base_url) or base_url
            nbhd_count = 0
            page = 1

            while page <= max_pages:
                try:
                    listings = await self._search_neighborhood(base_url, page)
                except Exception as exc:
                    logger.warning(
                        "StreetEasy search failed for %s page %d: %s",
                        neighborhood, page, exc,
                    )
                    break

                if not listings:
                    break

                new_in_page = 0
                for item in listings:
                    url = item.get("source_listing_id") or item.get("url")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_listings.append(item)
                        new_in_page += 1

                nbhd_count += new_in_page
                page += 1
                await asyncio.sleep(1.5)

            logger.info(
                "StreetEasy %s: %d listings across %d pages",
                neighborhood, nbhd_count, page - 1,
            )

        logger.info(
            "StreetEasy total: %d unique listings from %d neighborhoods",
            len(all_listings), len(self._search_urls),
        )
        return all_listings

    async def search_page(self, page: int = 1) -> tuple[list[Dict[str, Any]], bool]:
        """Multi-page interface used by ingestion.py.

        Delegates to search_all_locations on first call (handles all pagination
        internally per-neighborhood), then signals no more pages.
        """
        if page == 1:
            items = await self.search_all_locations()
            return items, False  # All done in one call
        return [], False

    async def get_details(self, listing_id: str) -> Dict[str, Any]:
        """Fetch and parse a StreetEasy detail page. listing_id is the full URL."""
        if not listing_id:
            return {}
        normalized_id = _normalize_streeteasy_url(listing_id) or listing_id
        try:
            html = await self._client.fetch(
                normalized_id,
                js_render=True,
                premium_proxy=True,
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
        data["source_listing_id"] = normalized_id
        if not data.get("url"):
            data["url"] = normalized_id

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
            data.setdefault("has_doorman_keywords", True)
        if re.search(r"\bgym\b|fitness", amenity_text):
            data.setdefault("has_gym_keywords", True)
        if re.search(r"parking|garage", amenity_text):
            data.setdefault("has_parking_keywords", True)
        if re.search(
            r"outdoor space|roof(?:top)? deck|sundeck|patio|terrace|balcony|garden|yard|courtyard",
            amenity_text,
        ):
            data.setdefault("has_outdoor_space_keywords", True)

    # Neighborhood from page
    if not data.get("neighborhood"):
        nbhd_el = soup.select_one(".nobreak, .BuildingInfo-neighborhood")
        if nbhd_el:
            data["neighborhood"] = nbhd_el.get_text(strip=True)


def _extract_card_data(soup: BeautifulSoup, listing_url: str) -> Dict[str, Any]:
    """Try to extract minimal listing data from a search card near the listing link."""
    data: Dict[str, Any] = {}
    target_path = urlsplit(listing_url).path.rstrip("/")

    def _href_matches(href: str | None) -> bool:
        if not href:
            return False
        full = urljoin(BASE_URL, href) if href.startswith("/") else href
        return urlsplit(full).path.rstrip("/") == target_path

    link = soup.find("a", href=_href_matches)
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
        return None
    slug = match.group(1)
    return SLUG_TO_NEIGHBORHOOD.get(slug, slug.replace("-", " ").title())


def _normalize_streeteasy_url(url: str) -> Optional[str]:
    if not url:
        return None
    url = url.strip()
    if not url:
        return None

    if url.startswith("/"):
        url = urljoin(BASE_URL, url)

    parts = urlsplit(url)
    if not parts.netloc or not parts.hostname:
        return None
    host = parts.hostname.lower()
    if host.startswith("www."):
        host = host[4:]
    if host != "streeteasy.com" and not host.endswith(".streeteasy.com"):
        return None

    netloc = host
    if parts.port:
        netloc = f"{host}:{parts.port}"

    if not _looks_like_streeteasy_listing_path(parts.path):
        return None

    clean = parts._replace(
        scheme="https",
        netloc=netloc,
        query="",
        fragment="",
        path=parts.path.rstrip("/"),
    )
    return urlunsplit(clean)


def _looks_like_streeteasy_listing_path(path: str) -> bool:
    segments = [segment for segment in path.strip("/").split("/") if segment]
    if len(segments) < 3 or segments[0] != "building":
        return False

    # Legacy format: /building/<slug>/<unit>/rental/<id>
    if len(segments) >= 5 and segments[-2] == "rental" and segments[-1].isdigit():
        return True

    # Current format: /building/<slug>/<unit>
    return len(segments) == 3


def _with_page_param(base_url: str, page: int) -> str:
    if page <= 1:
        return base_url
    parts = urlsplit(base_url)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != "page"]
    query.append(("page", str(page)))
    return urlunsplit(parts._replace(query=urlencode(query, doseq=True)))


def _with_search_filters(base_url: str, page: int = 1) -> str:
    """Add safe StreetEasy search filters (price + pagination)."""
    parts = urlsplit(base_url)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)]
    existing_keys = {k for k, _ in query}

    if "min_price" not in existing_keys and settings.SEARCH_PRICE_MIN:
        query.append(("min_price", str(settings.SEARCH_PRICE_MIN)))
    if "max_price" not in existing_keys and settings.SEARCH_PRICE_MAX:
        query.append(("max_price", str(settings.SEARCH_PRICE_MAX)))
    # StreetEasy bed/bath operator params are fragile when proxied through ZenRows URL encoding.
    # We intentionally avoid injecting those here and rely on downstream hard filters in matching.
    if page > 1:
        query = [(k, v) for k, v in query if k != "page"]
        query.append(("page", str(page)))

    return urlunsplit(parts._replace(query=urlencode(query, doseq=True)))


def _parse_price(text: str) -> Optional[float]:
    cleaned = text.replace(",", "").replace("$", "")
    match = re.search(r"\d+(?:\.\d+)?", cleaned)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None
