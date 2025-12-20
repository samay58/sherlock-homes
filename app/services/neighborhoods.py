"""Neighborhood normalization and lightweight SF neighborhood mapping."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class NeighborhoodBox:
    name: str
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    aliases: List[str]


FOCUS_NEIGHBORHOODS = [
    "Dolores Heights",
    "Potrero Hill",
    "Cole Valley",
    "Haight-Ashbury",
    "NoPa",
]


NEIGHBORHOOD_BOXES: List[NeighborhoodBox] = [
    NeighborhoodBox(
        name="Dolores Heights",
        lat_min=37.7540,
        lat_max=37.7665,
        lon_min=-122.4385,
        lon_max=-122.4245,
        aliases=["dolores heights", "dolores"],
    ),
    NeighborhoodBox(
        name="Potrero Hill",
        lat_min=37.7480,
        lat_max=37.7665,
        lon_min=-122.4165,
        lon_max=-122.3890,
        aliases=["potrero hill", "potrero", "portrero"],
    ),
    NeighborhoodBox(
        name="Cole Valley",
        lat_min=37.7600,
        lat_max=37.7725,
        lon_min=-122.4565,
        lon_max=-122.4450,
        aliases=["cole valley", "cole"],
    ),
    NeighborhoodBox(
        name="Haight-Ashbury",
        lat_min=37.7660,
        lat_max=37.7785,
        lon_min=-122.4525,
        lon_max=-122.4320,
        aliases=["haight-ashbury", "haight ashbury", "haight"],
    ),
    NeighborhoodBox(
        name="NoPa",
        lat_min=37.7720,
        lat_max=37.7825,
        lon_min=-122.4470,
        lon_max=-122.4270,
        aliases=["nopa", "no pa", "north of panhandle", "north panhandle"],
    ),
]


_GENERIC_NEIGHBORHOODS = {
    "san francisco",
    "sf",
    "san-francisco",
    "san francisco ca",
}


def normalize_neighborhood_name(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    cleaned = raw.strip().lower()
    if not cleaned or cleaned in _GENERIC_NEIGHBORHOODS:
        return None

    for box in NEIGHBORHOOD_BOXES:
        if cleaned == box.name.lower():
            return box.name
        for alias in box.aliases:
            if alias in cleaned:
                return box.name

    return raw.strip()


def normalize_neighborhood_list(names: Optional[List[str]]) -> Optional[List[str]]:
    if names is None:
        return None
    normalized: List[str] = []
    for item in names:
        if not item:
            continue
        canonical = normalize_neighborhood_name(item)
        if canonical and canonical not in normalized:
            normalized.append(canonical)
    return normalized if normalized else []


def neighborhood_from_coordinates(lat: Optional[float], lon: Optional[float]) -> Optional[str]:
    if lat is None or lon is None:
        return None
    for box in NEIGHBORHOOD_BOXES:
        if box.lat_min <= lat <= box.lat_max and box.lon_min <= lon <= box.lon_max:
            return box.name
    return None


def resolve_neighborhood(
    raw: Optional[str],
    lat: Optional[float],
    lon: Optional[float],
) -> Optional[str]:
    canonical = normalize_neighborhood_name(raw)
    if canonical:
        return canonical

    return neighborhood_from_coordinates(lat, lon)
