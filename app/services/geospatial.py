"""
Geospatial Intelligence Service for Sherlock Homes

Calculates location-based scores using only latitude/longitude data.
No external APIs required - uses static datasets for SF noise sources.
"""

import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class NoiseSource:
    """Represents a noise source with location and severity."""
    name: str
    coords: List[Tuple[float, float]]  # List of (lat, lon) points defining the line/area
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
        source_type="street"
    ),
    NoiseSource(
        name="Geary Blvd",
        coords=[(37.7852, -122.5034), (37.7852, -122.4034)],
        severity=0.85,
        source_type="street"
    ),
    NoiseSource(
        name="19th Avenue",
        coords=[(37.7815, -122.4759), (37.7215, -122.4759)],
        severity=0.85,
        source_type="street"
    ),
    NoiseSource(
        name="Mission Street",
        coords=[(37.7649, -122.4198), (37.7849, -122.4048)],
        severity=0.75,
        source_type="street"
    ),
    NoiseSource(
        name="Market Street",
        coords=[(37.7879, -122.4074), (37.7649, -122.4352)],
        severity=0.8,
        source_type="street"
    ),
    NoiseSource(
        name="Divisadero Street",
        coords=[(37.7849, -122.4399), (37.7449, -122.4399)],
        severity=0.65,
        source_type="street"
    ),
    NoiseSource(
        name="Lombard Street (Marina)",
        coords=[(37.8005, -122.4185), (37.8005, -122.4485)],
        severity=0.7,
        source_type="street"
    ),
    NoiseSource(
        name="Columbus Avenue",
        coords=[(37.7987, -122.4078), (37.8057, -122.4178)],
        severity=0.65,
        source_type="street"
    ),
    NoiseSource(
        name="Folsom Street",
        coords=[(37.7799, -122.4058), (37.7639, -122.4198)],
        severity=0.6,
        source_type="street"
    ),
    NoiseSource(
        name="Broadway",
        coords=[(37.7977, -122.4058), (37.7977, -122.4258)],
        severity=0.7,
        source_type="street"
    ),
]

SF_FREEWAYS = [
    NoiseSource(
        name="US-101 (Central)",
        coords=[(37.7749, -122.4094), (37.7649, -122.3994), (37.7549, -122.3894)],
        severity=1.0,
        source_type="freeway"
    ),
    NoiseSource(
        name="I-280",
        coords=[(37.7349, -122.4094), (37.7249, -122.4194), (37.7149, -122.4294)],
        severity=0.95,
        source_type="freeway"
    ),
    NoiseSource(
        name="I-80 (Bay Bridge approach)",
        coords=[(37.7879, -122.3894), (37.7879, -122.3794)],
        severity=0.95,
        source_type="freeway"
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

    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def point_to_segment_distance(
    point_lat: float, point_lon: float,
    seg_lat1: float, seg_lon1: float,
    seg_lat2: float, seg_lon2: float
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
    point_lat: float, point_lon: float,
    coords: List[Tuple[float, float]]
) -> float:
    """
    Calculate minimum distance from a point to a polyline (series of segments).
    Returns distance in meters.
    """
    if len(coords) < 2:
        if len(coords) == 1:
            return haversine_meters(point_lat, point_lon, coords[0][0], coords[0][1])
        return float('inf')

    min_dist = float('inf')
    for i in range(len(coords) - 1):
        dist = point_to_segment_distance(
            point_lat, point_lon,
            coords[i][0], coords[i][1],
            coords[i+1][0], coords[i+1][1]
        )
        min_dist = min(min_dist, dist)

    return min_dist


# =============================================================================
# TRANQUILITY SCORE CALCULATION
# =============================================================================

def calculate_tranquility_score(
    lat: Optional[float],
    lon: Optional[float]
) -> Dict:
    """
    Calculate a Tranquility Score (0-100) based on proximity to noise sources.

    Higher score = quieter location.

    Returns:
        {
            "score": int (0-100),
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
            "confidence": "low"
        }

    score = 100.0
    factors = {}
    warnings = []

    # Check busy street proximity
    min_street_dist = float('inf')
    nearest_street = None
    for street in SF_BUSY_STREETS:
        dist = distance_to_polyline(lat, lon, street.coords)
        if dist < min_street_dist:
            min_street_dist = dist
            nearest_street = street

    factors["nearest_busy_street"] = {
        "name": nearest_street.name if nearest_street else "Unknown",
        "distance_m": round(min_street_dist, 1)
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
    min_freeway_dist = float('inf')
    nearest_freeway = None
    for freeway in SF_FREEWAYS:
        dist = distance_to_polyline(lat, lon, freeway.coords)
        if dist < min_freeway_dist:
            min_freeway_dist = dist
            nearest_freeway = freeway

    factors["nearest_freeway"] = {
        "name": nearest_freeway.name if nearest_freeway else "None nearby",
        "distance_m": round(min_freeway_dist, 1)
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
    min_fire_dist = float('inf')
    nearest_fire = None
    for station in SF_FIRE_STATIONS:
        dist = haversine_meters(lat, lon, station["lat"], station["lon"])
        if dist < min_fire_dist:
            min_fire_dist = dist
            nearest_fire = station

    factors["nearest_fire_station"] = {
        "name": nearest_fire["name"] if nearest_fire else "Unknown",
        "distance_m": round(min_fire_dist, 1)
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
        "confidence": confidence
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


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def is_on_busy_street(lat: float, lon: float, threshold_meters: float = 50) -> bool:
    """Check if a location is directly on a busy street."""
    for street in SF_BUSY_STREETS:
        dist = distance_to_polyline(lat, lon, street.coords)
        if dist < threshold_meters:
            return True
    return False


def is_near_freeway(lat: float, lon: float, threshold_meters: float = 200) -> bool:
    """Check if a location is near a freeway."""
    for freeway in SF_FREEWAYS:
        dist = distance_to_polyline(lat, lon, freeway.coords)
        if dist < threshold_meters:
            return True
    return False
