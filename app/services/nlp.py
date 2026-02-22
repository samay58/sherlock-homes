from typing import List, Optional

KEYWORDS = {
    # Essential Attributes
    "natural_light": [
        # Direct mentions of light
        "natural light",
        "abundant light",
        "abundance of light",
        "bright",
        "sun-drenched",
        "light-filled",
        "luminous",
        "sunlit",
        "sun-soaked",
        "bathed in light",
        "floods of light",
        "flooded with light",
        "light and bright",
        "tons of light",
        "plenty of light",
        "ample light",
        "filled with light",
        "drenched in light",
        # Exposure/orientation
        "southern exposure",
        "western exposure",
        "south-facing",
        "west-facing",
        "east-facing",
        "southwest facing",
        # Windows
        "floor-to-ceiling windows",
        "floor to ceiling windows",
        "panoramic windows",
        "oversized windows",
        "large windows",
        "wall of windows",
        "expansive windows",
        "massive windows",
        "picture windows",
        "bay windows",
        "huge windows",
        # Architectural features
        "skylights",
        "skylight",
        "clerestory",
        "light well",
        "corner unit",
        "glass",
        "window wall",
        # Descriptive phrases
        "airy",
        "open and bright",
        "light and airy",
        "naturally lit",
        "sun fills",
        "sunshine",
        "daylight",
    ],
    "high_ceilings": [
        "high ceilings",
        "vaulted",
        "10 ft ceiling",
        "10-foot ceiling",
        "11 ft ceiling",
        "12 ft ceiling",
        "soaring",
        "cathedral",
        "coffered",
        "double-height",
        "dramatic ceiling",
        "tall ceiling",
        "lofty",
        "voluminous",
        "vertical space",
        "ceiling height",
    ],
    "outdoor_space": [
        # Basic outdoor features
        "balcony",
        "deck",
        "patio",
        "yard",
        "garden",
        "terrace",
        "rooftop",
        "outdoor",
        "outdoor space",
        "private outdoor",
        "backyard",
        "back yard",
        "front yard",
        "courtyard",
        # Enhanced descriptions
        "landscaped",
        "outdoor living",
        "al fresco",
        "outdoor entertaining",
        "bbq area",
        "fire pit",
        "outdoor kitchen",
        "outdoor fireplace",
        "deck space",
        "patio area",
        "deck area",
        "terrace space",
        # Quality indicators
        "private patio",
        "private balcony",
        "private deck",
        "large deck",
        "large patio",
        "spacious deck",
        "spacious patio",
        "wrap-around deck",
        "wraparound deck",
        "rooftop deck",
        "roof deck",
        "shared garden",
        "common garden",
    ],
    "parking": [
        "garage",
        "parking",
        "carport",
        "driveway",
        "off-street",
        "deeded parking",
        "1-car",
        "2-car",
        "tandem",
        "side-by-side",
        "attached garage",
        "detached garage",
        "parking space",
        "ev charging",
        "electric vehicle",
        "tesla charger",
    ],
    "view": [
        # General view terms
        "view",
        "views",
        "panoramic",
        "vista",
        "vistas",
        "overlook",
        "overlooks",
        "sweeping view",
        "stunning view",
        "spectacular view",
        "breathtaking view",
        "unobstructed view",
        # SF-specific landmarks
        "bay view",
        "ocean view",
        "golden gate",
        "bridge view",
        "coit tower",
        "alcatraz view",
        "twin peaks",
        # View types
        "cityscape",
        "city view",
        "downtown view",
        "skyline",
        "water view",
        "hill view",
        "park view",
        "tree-lined",
        "garden view",
        "courtyard view",
        "street view",
        # Quality descriptors
        "panoramic view",
        "180 degree",
        "270 degree",
        "360 degree",
        "floor to ceiling view",
        "walls of windows",
        "picture windows",
    ],
    "updated_systems": [
        "updated",
        "renovated",
        "remodeled",
        "new roof",
        "new hvac",
        "new plumbing",
        "new electrical",
        "new windows",
        "upgraded",
        "recent updates",
        "move-in ready",
        "turn-key",
        "newly",
        "modern systems",
        "central air",
        "central heat",
        "new furnace",
    ],
    "home_office": [
        "home office",
        "office",
        "study",
        "den",
        "workspace",
        "work from home",
        "wfh",
        "remote work",
        "zoom room",
        "dedicated office",
        "bonus room",
        "flex space",
        "third bedroom office",
        "converted bedroom",
        "office nook",
        "built-in desk",
    ],
    "storage": [
        "storage",
        "closet",
        "walk-in",
        "pantry",
        "built-in",
        "abundant storage",
        "attic",
        "basement",
        "crawl space",
        "shed",
        "workshop",
        "linen closet",
        "coat closet",
        "california closets",
        "custom closets",
        "organizational",
    ],
    "open_floor_plan": [
        "open floor",
        "open concept",
        "open plan",
        "open layout",
        "great room",
        "flowing",
        "seamless",
        "open kitchen",
        "kitchen opens to",
        "combined living",
        "loft-like",
        "spacious layout",
        "entertaining space",
        "connected spaces",
    ],
    "architectural_details": [
        "crown molding",
        "wainscoting",
        "hardwood",
        "exposed beam",
        "brick",
        "original detail",
        "period detail",
        "character",
        "charm",
        "architectural",
        "designer",
        "custom",
        "millwork",
        "built-in",
        "fireplace",
        "bay window",
        "french door",
        "pocket door",
        "transom",
        "restored",
        "preserved",
    ],
    # Quality Indicators
    "luxury": [
        "luxury",
        "luxurious",
        "high-end",
        "premium",
        "exclusive",
        "prestigious",
        "designer",
        "custom",
        "bespoke",
        "upscale",
        "sophisticated",
        "elegant",
        "refined",
        "exceptional",
        "extraordinary",
        "stunning",
        "magnificent",
        "exquisite",
    ],
    "designer": [
        "designer",
        "architect",
        "designed by",
        "custom design",
        "professionally designed",
        "interior designer",
        "staged",
        "curated",
        "thoughtfully designed",
        "magazine-worthy",
        "showplace",
        "showcase",
        "model home",
    ],
    "tech_ready": [
        "smart home",
        "nest",
        "ring",
        "automated",
        "smart",
        "fiber",
        "high-speed internet",
        "cat6",
        "wired",
        "security system",
        "video doorbell",
        "keyless entry",
        "app-controlled",
        "alexa",
        "google home",
        "homekit",
    ],
    # Deal Indicators (positive)
    "motivated_seller": [
        "motivated",
        "must sell",
        "bring offers",
        "priced to sell",
        "estate sale",
        "relocation",
        "transferred",
        "moving",
        "quick sale",
        "below market",
        "reduced",
        "price improvement",
        "back on market",
        "fell through",
        "previous buyer",
    ],
    # NYC rental features
    "pet_friendly": [
        "pet friendly",
        "pet-friendly",
        "pets allowed",
        "dogs allowed",
        "cats allowed",
        "dog friendly",
        "cat friendly",
        "pets welcome",
        "pet ok",
        "pet permitted",
        "pet fee",
        "pet deposit",
        "dog run",
        "pet spa",
        "pet grooming",
        "case-by-case",
    ],
    "no_pets": [
        "no pets",
        "no pet",
        "no-pet",
        "no dogs",
        "no cats",
        "no animals",
        "pet-free",
        "no pets allowed",
        "no-pet policy",
        "sorry no pets",
    ],
    "gym_fitness": [
        "fitness center",
        "gym",
        "fitness room",
        "weight room",
        "yoga studio",
        "peloton",
        "exercise room",
        "training room",
        "state-of-the-art fitness",
        "health club",
        "near gym",
        "gym nearby",
        "close to gym",
        "steps from gym",
        "block from gym",
        "walkable to gym",
        "equinox",
    ],
    "doorman_concierge": [
        "doorman",
        "full-time doorman",
        "24-hour doorman",
        "part-time doorman",
        "concierge",
        "lobby attendant",
        "virtual doorman",
        "attended lobby",
        "live-in super",
    ],
    "building_quality": [
        "boutique building",
        "well-maintained",
        "recently renovated",
        "landmark building",
        "elevator building",
        "prewar",
        "pre-war",
        "brownstone",
        "townhouse",
        "loft building",
        "condo-quality",
        "designer finishes",
        "spa-like",
    ],
    # Red Flags (negative indicators)
    "busy_street": [
        "busy street",
        "high traffic",
        "main road",
        "arterial",
        "commercial",
        "mixed use",
        "noise",
        "freeway",
        "highway",
        "broadway",
        "canal st",
        "houston st",
        "bowery",
        "delancey",
        "fdr drive",
        "bqe",
        "flatbush",
        "atlantic ave",
        "on the avenue",
    ],
    "foundation_issues": [
        "foundation",
        "settling",
        "cracks",
        "seismic",
        "retrofit needed",
        "soft story",
        "unreinforced",
        "structural",
        "sagging",
        "sloping floors",
        "uneven",
        "repair needed",
        "as-is",
        "fixer",
        "needs work",
        "tlc needed",
        "contractor special",
    ],
    "hoa_issues": [
        "litigation",
        "lawsuit",
        "special assessment",
        "hoa lawsuit",
        "pending litigation",
        "legal",
        "dispute",
        "high hoa",
        "hoa issues",
        "deferred maintenance",
        "reserves",
    ],
}

# Red flag detection keywords
RED_FLAGS = {
    "north_facing_only": [
        "north facing",
        "north-facing",
        "faces north",
        "northern exposure only",
    ],
    "basement_unit": [
        "garden level",
        "lower level",
        "basement",
        "below grade",
        "bottom unit",
    ],
    "tandem_parking": ["tandem", "tandem parking", "one behind"],
    "street_parking_only": ["street parking only", "no parking", "permit parking"],
}

# Positive sentiment boosters
POSITIVE_SIGNALS = {
    "rare": [
        "rare",
        "rarely available",
        "seldom",
        "unique opportunity",
        "once in a lifetime",
    ],
    "coveted": ["coveted", "sought-after", "desirable", "prime", "premier"],
    "quiet": [
        "quiet street",
        "tree-lined",
        "peaceful",
        "tranquil",
        "serene",
        "cul-de-sac",
    ],
    "walkable": ["walkable", "walk to", "steps from", "walking distance", "pedestrian"],
}


def extract_flags(text: str) -> dict[str, bool]:
    """Extract feature flags from property description text."""
    text_lower = text.lower()
    flags: dict[str, bool] = {}

    # Define valid flags that match PropertyListing model columns
    valid_positive_flags = [
        "natural_light",
        "high_ceilings",
        "outdoor_space",
        "parking",
        "view",
        "updated_systems",
        "home_office",
        "storage",
        "open_floor_plan",
        "architectural_details",
        "luxury",
        "designer",
        "tech_ready",
        "pet_friendly",
        "gym_fitness",
        "doorman_concierge",
        "building_quality",
    ]

    valid_red_flags = [
        "busy_street",
        "foundation_issues",
        "hoa_issues",
        "no_pets",
    ]

    # Check for positive features
    for key, terms in KEYWORDS.items():
        if key in valid_positive_flags:
            flags[key] = any(t in text_lower for t in terms)
        elif key in valid_red_flags:
            flags[key] = any(t in text_lower for t in terms)
        elif key == "motivated_seller":
            # Map motivated seller indicators to price reduction/back on market flags
            if any(t in text_lower for t in terms):
                if any(
                    t in text_lower
                    for t in ["reduced", "price improvement", "below market"]
                ):
                    flags["price_reduced"] = True
                if any(
                    t in text_lower
                    for t in ["back on market", "fell through", "previous buyer"]
                ):
                    flags["back_on_market"] = True

    # Check for additional red flags
    for key, terms in RED_FLAGS.items():
        if key == "north_facing_only":
            flags["north_facing_only"] = any(t in text_lower for t in terms)
        elif key == "basement_unit":
            flags["basement_unit"] = any(t in text_lower for t in terms)

    return flags


def calculate_text_quality_score(text: str, criteria: dict = None) -> float:
    """Calculate a quality score based on text analysis and criteria matching."""
    if not text:
        return 0.0

    text_lower = text.lower()
    score = 0.0

    # Default weights if no criteria weights provided
    default_weights = {
        "natural_light": 10,
        "outdoor_space": 8,
        "high_ceilings": 7,
        "parking": 6,
        "view": 9,
        "updated_systems": 7,
        "home_office": 5,
        "storage": 4,
        "open_floor_plan": 6,
        "architectural_details": 5,
        "luxury": 3,
        "designer": 3,
        "tech_ready": 4,
    }

    weights = (criteria.get("feature_weights") if criteria else None) or default_weights

    # Add points for positive features
    for key, terms in KEYWORDS.items():
        if any(t in text_lower for t in terms):
            score += weights.get(key, 1)

    # Add bonus for positive signals
    for key, terms in POSITIVE_SIGNALS.items():
        if any(t in text_lower for t in terms):
            score += 2

    # Subtract for red flags
    for key, terms in RED_FLAGS.items():
        if any(t in text_lower for t in terms):
            score -= 5

    # Normalize score to 0-100 range
    max_possible = sum(weights.values()) + (len(POSITIVE_SIGNALS) * 2)
    normalized_score = max(0, min(100, (score / max_possible) * 100))

    return normalized_score


# =============================================================================
# LIGHT POTENTIAL SCORING
# =============================================================================

# Keywords that indicate good light potential
LIGHT_POSITIVE_KEYWORDS = [
    "south-facing",
    "south facing",
    "southwest",
    "southwest-facing",
    "west-facing",
    "west facing",
    "western exposure",
    "southern exposure",
    "top floor",
    "top level",
    "upper floor",
    "penthouse",
    "corner unit",
    "corner apartment",
    "end unit",
    "floor-to-ceiling windows",
    "floor to ceiling windows",
    "wall of windows",
    "walls of windows",
    "panoramic windows",
    "skylights",
    "skylight",
    "clerestory",
    "bright",
    "sun-drenched",
    "sun-filled",
    "light-filled",
    "natural light",
    "floods of light",
    "bathed in light",
    "sunny",
    "sunlit",
    "luminous",
    "airy",
]

# Keywords that indicate poor light potential (heavy penalties)
LIGHT_NEGATIVE_KEYWORDS = [
    "north-facing",
    "north facing",
    "northern exposure",
    "faces north",
    "garden level",
    "basement",
    "lower level",
    "below grade",
    "bottom unit",
    "interior unit",
    "no view",
    "no natural light",
    "dark",
    "dimly lit",
    "limited light",
    "shaded",
    "windowless",
    "few windows",
    "small windows",
]


def estimate_light_potential(
    description: str = None,
    is_north_facing_only: bool = False,
    is_basement_unit: bool = False,
    has_natural_light_keywords: bool = False,
    photo_count: int = 0,
) -> dict:
    """
    Estimate light potential based on available signals.

    Since we cannot determine true solar orientation without building footprint data,
    we combine multiple heuristic signals to estimate light potential.

    Args:
        description: Property description text
        is_north_facing_only: Boolean flag from listing
        is_basement_unit: Boolean flag from listing
        has_natural_light_keywords: Boolean flag from listing
        photo_count: Number of photos (bright spaces tend to have more photos)

    Returns:
        {
            "score": int (0-100),
            "signals": List[str],
            "confidence": str ("high" | "medium" | "low"),
            "note": str  # Honest assessment
        }
    """
    score = 50  # Start neutral
    signals = []
    confidence = "medium"

    text_lower = (description or "").lower()

    # Check for positive light keywords
    positive_count = 0
    for keyword in LIGHT_POSITIVE_KEYWORDS:
        if keyword in text_lower:
            positive_count += 1
            if positive_count <= 3:  # Cap bonus
                signals.append(f"mentions '{keyword}'")

    # Add points for positive signals
    if positive_count > 0:
        bonus = min(25, positive_count * 5)  # Up to +25
        score += bonus

    # Check for negative light keywords
    negative_count = 0
    for keyword in LIGHT_NEGATIVE_KEYWORDS:
        if keyword in text_lower:
            negative_count += 1
            if negative_count <= 2:  # Cap logged signals
                signals.append(f"mentions '{keyword}'")

    # Subtract for negative signals
    if negative_count > 0:
        penalty = min(30, negative_count * 10)  # Up to -30
        score -= penalty

    # Use existing boolean flags (heavy weight - reliable)
    if has_natural_light_keywords:
        score += 15
        signals.append("natural_light_flag: true")

    if is_north_facing_only:
        score -= 25
        signals.append("north_facing_only: true")
        confidence = "high"  # We're confident this is BAD

    if is_basement_unit:
        score -= 30
        signals.append("basement_unit: true")
        confidence = "high"  # We're confident this is BAD

    # Heuristic: Top floor / penthouse bonus
    if (
        "top floor" in text_lower
        or "penthouse" in text_lower
        or "top level" in text_lower
    ):
        score += 10
        signals.append("top_floor_unit")

    # Heuristic: Corner unit bonus
    if "corner unit" in text_lower or "corner apartment" in text_lower:
        score += 8
        signals.append("corner_unit")

    # Heuristic: Many photos = bright space (owners photograph well-lit spaces)
    if photo_count >= 15:
        score += 5
        signals.append("high_photo_count")
    elif photo_count >= 10:
        score += 3

    # Clamp score to 0-100
    score = max(0, min(100, score))

    # Determine confidence level
    if is_basement_unit or is_north_facing_only:
        confidence = "high"
    elif len(signals) >= 3:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "score": int(round(score)),
        "signals": signals,
        "confidence": confidence,
        "note": "Light potential estimated from description keywords. True orientation cannot be determined from listing data.",
    }


def get_light_potential_tier(score: int) -> str:
    """Get human-readable tier for light potential score."""
    if score >= 75:
        return "Excellent"
    elif score >= 55:
        return "Good"
    elif score >= 35:
        return "Moderate"
    else:
        return "Limited"


def _unique_hits(text_lower: str, keywords: List[str]) -> List[str]:
    hits = [kw for kw in keywords if kw in text_lower]
    # Preserve order, remove duplicates
    seen = set()
    deduped: List[str] = []
    for hit in hits:
        if hit not in seen:
            deduped.append(hit)
            seen.add(hit)
    return deduped


def analyze_text_signals(text: str, nlp_config: dict) -> dict:
    """Analyze description text for buyer-specific positive/negative signals."""
    text_lower = (text or "").lower()
    positive = nlp_config.get("positive") or {}
    negative = nlp_config.get("negative") or {}

    positive_hits: dict[str, List[str]] = {}
    for group, payload in positive.items():
        keywords = payload.get("keywords") or []
        if keywords:
            hits = _unique_hits(text_lower, keywords)
            if hits:
                positive_hits[group] = hits

    negative_hits: dict[str, List[str]] = {}
    for group, payload in negative.items():
        keywords = payload.get("keywords") or []
        if keywords:
            hits = _unique_hits(text_lower, keywords)
            if hits:
                negative_hits[group] = hits

    # Context rules
    has_light_positive = bool(positive_hits.get("light"))
    if not has_light_positive and "dark" in negative_hits:
        pass
    else:
        negative_hits.pop("dark", None)

    return {
        "positive_hits": positive_hits,
        "negative_hits": negative_hits,
    }


def is_generic_description(text: str, positive_hits: Optional[dict] = None) -> bool:
    """Heuristic: short, low-signal descriptions are treated as generic."""
    if not text:
        return True
    words = text.split()
    if len(words) < 80:
        if not positive_hits:
            return True
        unique_groups = len([k for k, v in positive_hits.items() if v])
        return unique_groups < 2
    return False
