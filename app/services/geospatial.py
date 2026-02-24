"""
Geospatial Intelligence Service for Sherlock Homes

Calculates location-based scores using only latitude/longitude data.
No external APIs required - uses static datasets for SF and NYC noise sources.
"""

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class NoiseSource:
    """Represents a noise source with location and severity."""

    name: str
    coords: List[
        Tuple[float, float]
    ]  # List of (lat, lon) points defining the line/area
    severity: float  # 0.0 to 1.0, higher = noisier
    source_type: str  # 'street', 'freeway', 'transit', 'venue'


# =============================================================================
# SAN FRANCISCO NOISE SOURCE DATA
# =============================================================================

SF_BUSY_STREETS = [
    NoiseSource(
        name="Van Ness Ave",
        coords=[(37.7949, -122.4217), (37.7549, -122.4217)],
        severity=0.9,
        source_type="street",
    ),
    NoiseSource(
        name="Geary Blvd",
        coords=[(37.7852, -122.5034), (37.7852, -122.4034)],
        severity=0.85,
        source_type="street",
    ),
    NoiseSource(
        name="19th Avenue",
        coords=[(37.7815, -122.4759), (37.7215, -122.4759)],
        severity=0.85,
        source_type="street",
    ),
    NoiseSource(
        name="Mission Street",
        coords=[(37.7649, -122.4198), (37.7849, -122.4048)],
        severity=0.75,
        source_type="street",
    ),
    NoiseSource(
        name="Market Street",
        coords=[(37.7879, -122.4074), (37.7649, -122.4352)],
        severity=0.8,
        source_type="street",
    ),
    NoiseSource(
        name="Divisadero Street",
        coords=[(37.7849, -122.4399), (37.7449, -122.4399)],
        severity=0.65,
        source_type="street",
    ),
    NoiseSource(
        name="Lombard Street (Marina)",
        coords=[(37.8005, -122.4185), (37.8005, -122.4485)],
        severity=0.7,
        source_type="street",
    ),
    NoiseSource(
        name="Columbus Avenue",
        coords=[(37.7987, -122.4078), (37.8057, -122.4178)],
        severity=0.65,
        source_type="street",
    ),
    NoiseSource(
        name="Folsom Street",
        coords=[(37.7799, -122.4058), (37.7639, -122.4198)],
        severity=0.6,
        source_type="street",
    ),
    NoiseSource(
        name="Broadway",
        coords=[(37.7977, -122.4058), (37.7977, -122.4258)],
        severity=0.7,
        source_type="street",
    ),
]

SF_FREEWAYS = [
    NoiseSource(
        name="US-101 (Central)",
        coords=[(37.7749, -122.4094), (37.7649, -122.3994), (37.7549, -122.3894)],
        severity=1.0,
        source_type="freeway",
    ),
    NoiseSource(
        name="I-280",
        coords=[(37.7349, -122.4094), (37.7249, -122.4194), (37.7149, -122.4294)],
        severity=0.95,
        source_type="freeway",
    ),
    NoiseSource(
        name="I-80 (Bay Bridge approach)",
        coords=[(37.7879, -122.3894), (37.7879, -122.3794)],
        severity=0.95,
        source_type="freeway",
    ),
]

SF_FIRE_STATIONS = [
    # Major SF Fire Stations (sirens)
    {"name": "Station 1 (Embarcadero)", "lat": 37.7949, "lon": -122.3934},
    {"name": "Station 2 (Chinatown)", "lat": 37.7949, "lon": -122.4084},
    {"name": "Station 3 (Marina)", "lat": 37.8004, "lon": -122.4354},
    {"name": "Station 7 (Mission)", "lat": 37.7629, "lon": -122.4154},
    {"name": "Station 10 (Potrero)", "lat": 37.7579, "lon": -122.3994},
    {"name": "Station 13 (SOMA)", "lat": 37.7829, "lon": -122.4034},
    {"name": "Station 36 (Castro)", "lat": 37.7619, "lon": -122.4354},
    {"name": "Station 38 (Noe Valley)", "lat": 37.7519, "lon": -122.4324},
]


# =============================================================================
# NEW YORK CITY NOISE SOURCE DATA
# =============================================================================

NYC_BUSY_STREETS = [
    NoiseSource(
        name="Broadway (Manhattan)",
        coords=[(40.7061, -74.0131), (40.7580, -73.9855), (40.7831, -73.9712)],
        severity=0.85,
        source_type="street",
    ),
    NoiseSource(
        name="Canal Street",
        coords=[(40.7195, -74.0066), (40.7166, -73.9982), (40.7149, -73.9909)],
        severity=0.9,
        source_type="street",
    ),
    NoiseSource(
        name="Houston Street",
        coords=[(40.7268, -74.0078), (40.7227, -73.9952), (40.7209, -73.9828)],
        severity=0.8,
        source_type="street",
    ),
    NoiseSource(
        name="Bowery",
        coords=[(40.7149, -73.9974), (40.7242, -73.9927), (40.7316, -73.9892)],
        severity=0.75,
        source_type="street",
    ),
    NoiseSource(
        name="Delancey Street",
        coords=[(40.7188, -73.9989), (40.7178, -73.9878), (40.7148, -73.9778)],
        severity=0.85,
        source_type="street",
    ),
    NoiseSource(
        name="Flatbush Avenue",
        coords=[(40.6905, -73.9764), (40.6832, -73.9773), (40.6705, -73.9631)],
        severity=0.8,
        source_type="street",
    ),
    NoiseSource(
        name="Atlantic Avenue (Brooklyn)",
        coords=[(40.6863, -73.9781), (40.6848, -73.9685), (40.6822, -73.9549)],
        severity=0.75,
        source_type="street",
    ),
    NoiseSource(
        name="4th Avenue (Brooklyn)",
        coords=[(40.6863, -73.9781), (40.6746, -73.9831), (40.6656, -73.9880)],
        severity=0.7,
        source_type="street",
    ),
]

NYC_FREEWAYS = [
    NoiseSource(
        name="BQE (Brooklyn-Queens Expressway)",
        coords=[
            (40.6891, -73.9979), (40.6938, -73.9923), (40.6996, -73.9862),
            (40.7024, -73.9847),
        ],
        severity=1.0,
        source_type="freeway",
    ),
    NoiseSource(
        name="FDR Drive",
        coords=[
            (40.7096, -73.9752), (40.7210, -73.9740), (40.7350, -73.9730),
            (40.7550, -73.9660),
        ],
        severity=0.95,
        source_type="freeway",
    ),
]

NYC_FIRE_STATIONS = [
    {"name": "FDNY Engine 205/Ladder 118 (DUMBO)", "lat": 40.6988, "lon": -73.9872},
    {"name": "FDNY Engine 224 (Brooklyn Heights)", "lat": 40.6933, "lon": -73.9930},
    {"name": "FDNY Engine 229 (Williamsburg)", "lat": 40.7114, "lon": -73.9572},
    {"name": "FDNY Engine 207/Ladder 110 (Fort Greene)", "lat": 40.6898, "lon": -73.9753},
    {"name": "FDNY Engine 33/Ladder 9 (East Village)", "lat": 40.7274, "lon": -73.9876},
    {"name": "FDNY Engine 55 (SoHo)", "lat": 40.7230, "lon": -73.9985},
    {"name": "FDNY Engine 24/Ladder 5 (Chelsea)", "lat": 40.7395, "lon": -73.9998},
    {"name": "FDNY Engine 14 (East Village/Gramercy)", "lat": 40.7322, "lon": -73.9859},
]


def _is_in_nyc(lat: float, lon: float) -> bool:
    """Check if coordinates fall within the NYC coverage bounding box."""
    return 40.62 <= lat <= 40.80 and -74.05 <= lon <= -73.90


# =============================================================================
# DISTANCE CALCULATIONS
# =============================================================================


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance in meters between two points.
    Uses the Haversine formula.
    """
    R = 6371000  # Earth's radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def point_to_segment_distance(
    point_lat: float,
    point_lon: float,
    seg_lat1: float,
    seg_lon1: float,
    seg_lat2: float,
    seg_lon2: float,
) -> float:
    """
    Calculate the minimum distance from a point to a line segment.
    Returns distance in meters.

    Uses projection onto the line segment to find the closest point.
    """
    # Vector from segment start to point
    px = point_lon - seg_lon1
    py = point_lat - seg_lat1

    # Vector of segment
    sx = seg_lon2 - seg_lon1
    sy = seg_lat2 - seg_lat1

    # Segment length squared (avoid sqrt for comparison)
    seg_len_sq = sx * sx + sy * sy

    if seg_len_sq == 0:
        # Segment is a point
        return haversine_meters(point_lat, point_lon, seg_lat1, seg_lon1)

    # Project point onto segment line, clamped to [0, 1]
    t = max(0, min(1, (px * sx + py * sy) / seg_len_sq))

    # Closest point on segment
    closest_lon = seg_lon1 + t * sx
    closest_lat = seg_lat1 + t * sy

    return haversine_meters(point_lat, point_lon, closest_lat, closest_lon)


def distance_to_polyline(
    point_lat: float, point_lon: float, coords: List[Tuple[float, float]]
) -> float:
    """
    Calculate minimum distance from a point to a polyline (series of segments).
    Returns distance in meters.
    """
    if len(coords) < 2:
        if len(coords) == 1:
            return haversine_meters(point_lat, point_lon, coords[0][0], coords[0][1])
        return float("inf")

    min_dist = float("inf")
    for i in range(len(coords) - 1):
        dist = point_to_segment_distance(
            point_lat,
            point_lon,
            coords[i][0],
            coords[i][1],
            coords[i + 1][0],
            coords[i + 1][1],
        )
        min_dist = min(min_dist, dist)

    return min_dist


# =============================================================================
# TRANQUILITY SCORE CALCULATION
# =============================================================================


def _is_in_sf(lat: float, lon: float) -> bool:
    """Check if coordinates fall within the San Francisco bounding box."""
    return 37.707 <= lat <= 37.83 and -122.515 <= lon <= -122.355


def calculate_tranquility_score(lat: Optional[float], lon: Optional[float]) -> Dict:
    """
    Calculate a Tranquility Score (0-100) based on proximity to noise sources.

    Higher score = quieter location. Covers SF and NYC noise sources.
    Returns None score for locations outside both coverage areas.

    Returns:
        {
            "score": int (0-100) or None,
            "factors": {
                "nearest_busy_street": {"name": str, "distance_m": float},
                "nearest_freeway": {"name": str, "distance_m": float},
                "nearest_fire_station": {"name": str, "distance_m": float},
            },
            "warnings": List[str],
            "confidence": str ("high" | "medium" | "low")
        }
    """
    if lat is None or lon is None:
        return {
            "score": 50,  # Neutral if no data
            "factors": {},
            "warnings": ["No location data available"],
            "confidence": "low",
        }

    # Select city-specific noise data
    if _is_in_sf(lat, lon):
        busy_streets = SF_BUSY_STREETS
        freeways = SF_FREEWAYS
        fire_stations = SF_FIRE_STATIONS
    elif _is_in_nyc(lat, lon):
        busy_streets = NYC_BUSY_STREETS
        freeways = NYC_FREEWAYS
        fire_stations = NYC_FIRE_STATIONS
    else:
        return {
            "score": None,
            "factors": {},
            "warnings": ["Outside coverage area"],
            "confidence": "low",
        }

    score = 100.0
    factors = {}
    warnings = []

    # Check busy street proximity
    min_street_dist = float("inf")
    nearest_street = None
    for street in busy_streets:
        dist = distance_to_polyline(lat, lon, street.coords)
        if dist < min_street_dist:
            min_street_dist = dist
            nearest_street = street

    factors["nearest_busy_street"] = {
        "name": nearest_street.name if nearest_street else "Unknown",
        "distance_m": round(min_street_dist, 1),
    }

    # Deduct for busy street proximity (weighted by severity)
    if nearest_street:
        severity = nearest_street.severity
        if min_street_dist < 30:  # On the street
            score -= 35 * severity
            warnings.append(f"On {nearest_street.name} (high traffic)")
        elif min_street_dist < 75:  # ~1/2 block
            score -= 25 * severity
            warnings.append(f"Near {nearest_street.name}")
        elif min_street_dist < 150:  # ~1 block
            score -= 15 * severity
        elif min_street_dist < 300:  # ~2 blocks
            score -= 8 * severity

    # Check freeway proximity (severe penalty)
    min_freeway_dist = float("inf")
    nearest_freeway = None
    for freeway in freeways:
        dist = distance_to_polyline(lat, lon, freeway.coords)
        if dist < min_freeway_dist:
            min_freeway_dist = dist
            nearest_freeway = freeway

    factors["nearest_freeway"] = {
        "name": nearest_freeway.name if nearest_freeway else "None nearby",
        "distance_m": round(min_freeway_dist, 1),
    }

    if nearest_freeway and min_freeway_dist < 500:
        if min_freeway_dist < 100:
            score -= 40
            warnings.append(f"Adjacent to {nearest_freeway.name}")
        elif min_freeway_dist < 200:
            score -= 30
            warnings.append(f"Very close to {nearest_freeway.name}")
        elif min_freeway_dist < 300:
            score -= 20
        elif min_freeway_dist < 500:
            score -= 10

    # Check fire station proximity (siren noise)
    min_fire_dist = float("inf")
    nearest_fire = None
    for station in fire_stations:
        dist = haversine_meters(lat, lon, station["lat"], station["lon"])
        if dist < min_fire_dist:
            min_fire_dist = dist
            nearest_fire = station

    factors["nearest_fire_station"] = {
        "name": nearest_fire["name"] if nearest_fire else "Unknown",
        "distance_m": round(min_fire_dist, 1),
    }

    if min_fire_dist < 150:
        score -= 10
        warnings.append(f"Near {nearest_fire['name']}")
    elif min_fire_dist < 300:
        score -= 5

    # Determine confidence based on data quality
    confidence = "high" if min_street_dist < 500 else "medium"

    return {
        "score": max(0, min(100, int(round(score)))),
        "factors": factors,
        "warnings": warnings,
        "confidence": confidence,
    }


def get_tranquility_tier(score: int) -> str:
    """Get human-readable tier for tranquility score."""
    if score >= 80:
        return "Very Quiet"
    elif score >= 60:
        return "Quiet"
    elif score >= 40:
        return "Moderate"
    elif score >= 20:
        return "Noisy"
    else:
        return "Very Noisy"


def apply_location_modifiers(
    address: Optional[str],
    description: Optional[str],
    modifiers: Dict[str, Any],
    has_busy_street: bool = False,
    noise_hits: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Apply street-level boosts/penalties and conditions from buyer config."""
    address_lower = (address or "").lower()
    text_lower = (description or "").lower()
    evidence: List[str] = []
    adjustment = 0.0

    penalized_street = False

    for street in modifiers.get("boost_streets", []) or []:
        if street.lower() in address_lower:
            adjustment += 1.5
            evidence.append(f"boost street {street}")

    for street in modifiers.get("penalize_streets", []) or []:
        if street.lower() in address_lower:
            penalized_street = True
            adjustment -= 1.5
            evidence.append(f"penalize street {street}")

    conditions = set(modifiers.get("penalize_conditions", []) or [])
    if "adjacent_to_bar" in conditions and (
        noise_hits or "bar" in text_lower or "nightlife" in text_lower
    ):
        adjustment -= 1.5
        evidence.append("adjacent to nightlife")
    if "on_major_thoroughfare" in conditions and (has_busy_street or penalized_street):
        adjustment -= 1.5
        evidence.append("major thoroughfare exposure")
    if "first_floor_busy_street" in conditions:
        if ("first floor" in text_lower or "ground floor" in text_lower) and (
            has_busy_street or penalized_street
        ):
            adjustment -= 1.0
            evidence.append("first floor on busy street")

    return {
        "adjustment": adjustment,
        "evidence": evidence,
        "penalized_street": penalized_street,
    }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def is_on_busy_street(lat: float, lon: float, threshold_meters: float = 50) -> bool:
    """Check if a location is directly on a busy street."""
    streets = SF_BUSY_STREETS
    if _is_in_nyc(lat, lon):
        streets = NYC_BUSY_STREETS
    for street in streets:
        dist = distance_to_polyline(lat, lon, street.coords)
        if dist < threshold_meters:
            return True
    return False


def is_near_freeway(lat: float, lon: float, threshold_meters: float = 200) -> bool:
    """Check if a location is near a freeway."""
    freeways = SF_FREEWAYS
    if _is_in_nyc(lat, lon):
        freeways = NYC_FREEWAYS
    for freeway in freeways:
        dist = distance_to_polyline(lat, lon, freeway.coords)
        if dist < threshold_meters:
            return True
    return False
