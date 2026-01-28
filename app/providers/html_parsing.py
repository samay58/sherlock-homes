from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Iterable, List, Optional

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

LISTING_TYPES = {
    "Apartment",
    "Condominium",
    "House",
    "SingleFamilyResidence",
    "Residence",
    "Townhouse",
    "Product",
}


def extract_item_list_urls(html: str) -> List[str]:
    urls: List[str] = []
    for obj in _extract_json_ld_objects(html):
        types = _as_list(obj.get("@type"))
        if "ItemList" not in types:
            continue
        for item in obj.get("itemListElement") or []:
            if not isinstance(item, dict):
                continue
            url = item.get("url")
            if not url and isinstance(item.get("item"), dict):
                url = item["item"].get("url")
            if url:
                urls.append(url)
    return _dedupe(urls)


def parse_listing_from_html(html: str) -> Dict[str, Any]:
    listing = _select_listing_candidate(_extract_json_ld_objects(html))
    data: Dict[str, Any] = _normalize_listing(listing) if listing else {}

    soup = BeautifulSoup(html, "html.parser")
    if not data.get("description"):
        data["description"] = _meta_content(
            soup,
            properties=["og:description"],
            names=["description"],
        )
    if not data.get("address"):
        data["address"] = _meta_content(soup, properties=["og:title"])
    if not data.get("photos"):
        og_image = _meta_content(soup, properties=["og:image"])
        if og_image:
            data["photos"] = [og_image]

    if data.get("lat") is None or data.get("lon") is None:
        lat = _meta_content(soup, properties=["place:location:latitude", "og:latitude"])
        lon = _meta_content(
            soup, properties=["place:location:longitude", "og:longitude"]
        )
        data["lat"] = _parse_float(lat) if lat else data.get("lat")
        data["lon"] = _parse_float(lon) if lon else data.get("lon")

    return {k: v for k, v in data.items() if v is not None}


def extract_embedded_property_data(html: str) -> Dict[str, Any]:
    best: Optional[Dict[str, Any]] = None
    best_score = 0
    for obj in _extract_embedded_json_objects(html):
        candidate = _find_best_property_dict(obj)
        if not candidate:
            continue
        score = _property_score(candidate)
        if score > best_score:
            best_score = score
            best = candidate
    if not best or best_score < 3:
        return {}
    data = _normalize_embedded_listing(best)
    return {k: v for k, v in data.items() if v is not None}


def merge_listing_fields(base: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in extra.items():
        if value is None:
            continue
        existing = merged.get(key)
        if existing is None or existing == [] or existing == "":
            merged[key] = value
    return merged


def _extract_json_ld_objects(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    objects: List[Dict[str, Any]] = []
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text()
        if not raw:
            continue
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.debug("Skipping invalid JSON-LD block")
            continue
        for obj in _flatten_json_ld(data):
            if isinstance(obj, dict):
                objects.append(obj)
    return objects


def _extract_embedded_json_objects(html: str) -> List[Dict[str, Any]]:
    objects: List[Dict[str, Any]] = []
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", id="__NEXT_DATA__"):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        objects.append(data)

    for var_name in ("__PRELOADED_STATE__", "__INITIAL_STATE__"):
        extracted = _extract_window_json(html, var_name)
        if extracted:
            objects.append(extracted)

    return objects


def _flatten_json_ld(data: Any) -> Iterable[Any]:
    if isinstance(data, list):
        for item in data:
            yield from _flatten_json_ld(item)
        return
    if isinstance(data, dict):
        if "@graph" in data:
            yield from _flatten_json_ld(data["@graph"])
        else:
            yield data


def _select_listing_candidate(
    objects: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    best: Optional[Dict[str, Any]] = None
    best_score = -1
    for obj in objects:
        types = _as_list(obj.get("@type"))
        has_type = any(t in LISTING_TYPES for t in types)
        if not has_type and not obj.get("address") and not obj.get("offers"):
            continue

        score = 0
        if obj.get("address"):
            score += 1
        if obj.get("offers") or obj.get("price"):
            score += 1
        if obj.get("geo"):
            score += 1
        if obj.get("image"):
            score += 1
        if has_type:
            score += 1

        if score > best_score:
            best = obj
            best_score = score
    return best


def _find_best_property_dict(data: Any) -> Optional[Dict[str, Any]]:
    best: Optional[Dict[str, Any]] = None
    best_score = 0
    visited = 0
    stack: List[tuple[Any, int]] = [(data, 0)]
    while stack:
        node, depth = stack.pop()
        visited += 1
        if visited > 20000:
            break
        if isinstance(node, dict):
            score = _property_score(node)
            if score > best_score:
                best = node
                best_score = score
            if depth < 8:
                for value in node.values():
                    stack.append((value, depth + 1))
        elif isinstance(node, list) and depth < 8:
            for value in node:
                stack.append((value, depth + 1))
    return best


def _normalize_listing(obj: Dict[str, Any]) -> Dict[str, Any]:
    address = _format_address(obj.get("address"))
    offers = obj.get("offers") or {}
    if isinstance(offers, list) and offers:
        offers = offers[0]

    price = _first_present([obj.get("price"), offers.get("price")])
    beds = _first_present([obj.get("numberOfBedrooms"), obj.get("numberOfRooms")])
    baths = _first_present(
        [
            obj.get("numberOfBathroomsTotal"),
            obj.get("numberOfBathrooms"),
            obj.get("bathroomCount"),
        ]
    )
    floor_size = obj.get("floorSize") or obj.get("floor_size")
    if isinstance(floor_size, dict):
        floor_size = floor_size.get("value") or floor_size.get("size")

    geo = obj.get("geo") or {}
    if isinstance(geo, list) and geo:
        geo = geo[0]

    images = obj.get("image") or obj.get("images") or []
    if isinstance(images, str):
        images = [images]
    elif not isinstance(images, list):
        images = []

    property_type = _first_present([obj.get("category"), obj.get("@type")])
    if isinstance(property_type, list):
        property_type = next(
            (value for value in property_type if value in LISTING_TYPES),
            property_type[0],
        )

    return {
        "address": address,
        "price": _parse_float(price),
        "beds": _parse_int(beds),
        "baths": _parse_float(baths),
        "sqft": _parse_int(floor_size),
        "lat": _parse_float(geo.get("latitude") if isinstance(geo, dict) else None),
        "lon": _parse_float(geo.get("longitude") if isinstance(geo, dict) else None),
        "description": obj.get("description"),
        "photos": [img for img in images if isinstance(img, str)],
        "property_type": property_type if isinstance(property_type, str) else None,
        "url": obj.get("url"),
        "year_built": _parse_int(obj.get("yearBuilt")),
    }


def _normalize_embedded_listing(obj: Dict[str, Any]) -> Dict[str, Any]:
    address = _extract_address(
        obj.get("address") or obj.get("fullAddress") or obj.get("addressLine")
    )
    price = _extract_numeric(
        obj, ["price", "listPrice", "listingPrice", "priceValue", "list_price"]
    )
    beds = _extract_numeric(obj, ["beds", "bedrooms", "bedroomCount", "bedroom_count"])
    baths = _extract_numeric(
        obj, ["baths", "bathrooms", "bathroomCount", "bathroom_count"]
    )
    sqft = _extract_numeric(
        obj, ["sqft", "livingArea", "living_area", "livingAreaSize", "living_area_size"]
    )
    lat = _extract_numeric(obj, ["lat", "latitude"])
    lon = _extract_numeric(obj, ["lon", "lng", "longitude"])
    description = _extract_text(obj, ["description", "remarks", "summary"])
    year_built = _extract_numeric(obj, ["yearBuilt", "year_built"])
    images = _extract_images(
        obj.get("photos")
        or obj.get("images")
        or obj.get("media")
        or obj.get("photoUrls")
    )

    return {
        "address": address,
        "price": _parse_float(price),
        "beds": _parse_int(beds),
        "baths": _parse_float(baths),
        "sqft": _parse_int(sqft),
        "lat": _parse_float(lat),
        "lon": _parse_float(lon),
        "description": description,
        "photos": images,
        "year_built": _parse_int(year_built),
    }


def _meta_content(
    soup: BeautifulSoup,
    *,
    properties: Optional[List[str]] = None,
    names: Optional[List[str]] = None,
) -> Optional[str]:
    for prop in properties or []:
        tag = soup.find("meta", property=prop)
        if tag and tag.get("content"):
            return str(tag["content"]).strip()
    for name in names or []:
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return str(tag["content"]).strip()
    return None


def _format_address(value: Any) -> Optional[str]:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        parts = [
            value.get("streetAddress")
            or value.get("street")
            or value.get("streetLine"),
            value.get("addressLocality") or value.get("city"),
            value.get("addressRegion") or value.get("state"),
            value.get("postalCode") or value.get("zip"),
        ]
        return ", ".join([part for part in parts if part])
    return None


def _extract_address(value: Any) -> Optional[str]:
    if isinstance(value, dict):
        return _format_address(value)
    if isinstance(value, str):
        return value.strip()
    return None


def _extract_numeric(obj: Dict[str, Any], keys: List[str]) -> Any:
    for key in keys:
        if key in obj and obj[key] is not None:
            value = obj[key]
            if isinstance(value, dict):
                value = value.get("value") or value.get("amount") or value.get("number")
            return value
    return None


def _extract_text(obj: Dict[str, Any], keys: List[str]) -> Optional[str]:
    for key in keys:
        value = obj.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _extract_images(value: Any) -> List[str]:
    images: List[str] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                images.append(item)
            elif isinstance(item, dict):
                url = item.get("url") or item.get("href")
                if isinstance(url, str):
                    images.append(url)
    elif isinstance(value, dict):
        url = value.get("url") or value.get("href")
        if isinstance(url, str):
            images.append(url)
    elif isinstance(value, str):
        images.append(value)
    return [img for img in images if isinstance(img, str)]


def _parse_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace(",", "")
        match = re.search(r"-?\d+(\.\d+)?", cleaned)
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return None
    return None


def _parse_int(value: Any) -> Optional[int]:
    parsed = _parse_float(value)
    if parsed is None:
        return None
    return int(parsed)


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _first_present(values: List[Any]) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _dedupe(values: List[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _property_score(obj: Dict[str, Any]) -> int:
    score = 0
    if obj.get("address") or obj.get("fullAddress") or obj.get("addressLine"):
        score += 1
    if obj.get("price") or obj.get("listPrice") or obj.get("listingPrice"):
        score += 1
    if obj.get("beds") or obj.get("bedrooms") or obj.get("bedroomCount"):
        score += 1
    if obj.get("baths") or obj.get("bathrooms") or obj.get("bathroomCount"):
        score += 1
    if obj.get("sqft") or obj.get("livingArea") or obj.get("livingAreaSize"):
        score += 1
    if obj.get("lat") or obj.get("latitude") or obj.get("lon") or obj.get("longitude"):
        score += 1
    if obj.get("photos") or obj.get("images") or obj.get("media"):
        score += 1
    return score


def _extract_window_json(html: str, var_name: str) -> Optional[Dict[str, Any]]:
    marker = f"window.{var_name}"
    idx = html.find(marker)
    if idx == -1:
        return None
    eq = html.find("=", idx)
    if eq == -1:
        return None
    brace = html.find("{", eq)
    if brace == -1:
        return None
    raw = _extract_balanced_json(html, brace)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _extract_balanced_json(text: str, start: int) -> Optional[str]:
    depth = 0
    in_string = False
    escape = False
    for idx in range(start, len(text)):
        char = text[idx]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
        else:
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start : idx + 1]
    return None
