from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

CRITERION_LABELS = {
    "natural_light": "Natural light",
    "outdoor_space": "Outdoor space",
    "character_soul": "Character & soul",
    "kitchen_quality": "Kitchen quality",
    "location_quiet": "Quiet location",
    "office_space": "Office space",
    "indoor_outdoor_flow": "Indoor-outdoor flow",
    "high_ceilings": "High ceilings",
    "layout_intelligence": "Layout intelligence",
    "move_in_ready": "Move-in ready",
    "views": "Views",
    "in_unit_laundry": "In-unit laundry",
    "parking": "Parking",
    "central_hvac": "Central HVAC",
    "gas_stove": "Gas stove",
    "dishwasher": "Dishwasher",
    "storage": "Storage",
    "pet_friendly": "Pet friendly",
    "gym_fitness": "Gym / fitness",
    "building_quality": "Building quality",
    "doorman_concierge": "Doorman / concierge",
}

TIER_THRESHOLDS = [
    (80, "Exceptional"),
    (70, "Strong"),
    (60, "Interesting"),
    (0, "Pass"),
]

OFFICE_KEYWORDS = [
    "home office",
    "office",
    "study",
    "den",
    "workspace",
    "work from home",
    "wfh",
    "dedicated office",
    "bonus room",
]

INDOOR_OUTDOOR_KEYWORDS = [
    "indoor-outdoor",
    "indoor outdoor",
    "folding doors",
    "sliding doors",
    "opens to",
    "seamless",
    "flow to",
    "outdoor entertaining",
]

LAYOUT_KEYWORDS = [
    "open layout",
    "open floor plan",
    "open concept",
    "great room",
    "well laid out",
    "good flow",
    "functional layout",
    "spacious layout",
    "loft-like",
    "loft style",
    "wide open",
    "expansive",
    "sprawling",
    "generously proportioned",
    "wide layout",
    "spacious living",
    "oversized living",
    "large living",
    "open living",
    "live/work",
]

LAYOUT_NEGATIVE_KEYWORDS = [
    "awkward layout",
    "odd layout",
    "railroad",
    "chopped up",
    "low ceiling",
    "low ceilings",
    "narrow",
    "narrow hallway",
    "tight layout",
    "cramped",
    "compact layout",
]

LAUNDRY_KEYWORDS = [
    "in-unit laundry",
    "in unit laundry",
    "washer/dryer",
    "washer dryer",
    "laundry in unit",
    "stackable washer",
    "laundry closet",
]

LAUNDRY_BUILDING_KEYWORDS = [
    "laundry in building",
    "shared laundry",
    "common laundry",
]

CENTRAL_HVAC_KEYWORDS = [
    "central air",
    "central a/c",
    "central ac",
    "forced air",
    "central heat",
    "hvac",
]

GAS_STOVE_KEYWORDS = [
    "gas range",
    "gas stove",
    "gas cooktop",
    "gas burner",
]

DISHWASHER_KEYWORDS = [
    "dishwasher",
    "bosch",
    "miele",
]

PARKING_STREET_ONLY_KEYWORDS = [
    "street parking only",
    "permit parking",
    "no garage",
]

NO_PARKING_KEYWORDS = [
    "no parking",
    "parking not available",
]


@dataclass
class ScoreComponent:
    score: float
    weight: float
    confidence: str
    evidence: List[str]


@dataclass
class MatchSignals:
    tranquility_score: Optional[float] = None
    light_potential: Optional[float] = None
    visual_quality: Optional[float] = None
    nlp_character_score: Optional[float] = None


def _score_from_hits(hit_count: int, max_hits: int = 4) -> float:
    if hit_count <= 0:
        return 0.0
    return min(10.0, (hit_count / max_hits) * 10.0)


def _blend_scores(values: List[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _score_tier(score_percent: float) -> str:
    """Assign tier based on percentage score (0-100)."""
    for threshold, label in TIER_THRESHOLDS:
        if score_percent >= threshold:
            return label
    return "Pass"


def _score_percent(total_points: float, total_possible: float) -> str:
    if total_possible <= 0:
        return "0%"
    percent = round((total_points / total_possible) * 100)
    return f"{percent}%"


def _find_hits(text_lower: str, keywords: List[str]) -> List[str]:
    hits = [kw for kw in keywords if kw in text_lower]
    deduped: List[str] = []
    seen = set()
    for hit in hits:
        if hit not in seen:
            deduped.append(hit)
            seen.add(hit)
    return deduped


def _soft_cap_penalty(
    price: Optional[float], soft_price: Optional[float], hard_price: Optional[float]
) -> float:
    if price is None or soft_price is None:
        return 0.0
    hard_price = hard_price or soft_price
    if price <= soft_price:
        return 0.0
    if price >= hard_price:
        return 10.0
    span = hard_price - soft_price
    if span <= 0:
        return 10.0
    return 10.0 * ((price - soft_price) / span)


def _hoa_penalty(hoa_fee: Optional[float]) -> float:
    if hoa_fee is None:
        return 0.0
    if hoa_fee < 400:
        return 0.0
    if hoa_fee <= 800:
        return 0.0
    if hoa_fee <= 1000:
        return 5.0
    return 10.0
