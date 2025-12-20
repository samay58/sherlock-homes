from pydantic import BaseModel, HttpUrl, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class PropertyListingBase(BaseModel):
    address: str
    price: Optional[float] = None
    beds: Optional[int] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    property_type: Optional[str] = None
    url: Optional[HttpUrl] = None
    listing_id: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    year_built: Optional[int] = None
    listing_status: Optional[str] = None
    description: Optional[str] = None
    neighborhood: Optional[str] = None
    days_on_market: Optional[int] = None

    # Feature flags (from NLP analysis) - no aliases, use actual field names
    has_natural_light_keywords: bool = False
    has_high_ceiling_keywords: bool = False
    has_outdoor_space_keywords: bool = False
    has_parking_keywords: bool = False
    has_view_keywords: bool = False
    has_updated_systems_keywords: bool = False
    has_home_office_keywords: bool = False
    has_storage_keywords: bool = False
    has_open_floor_plan_keywords: bool = False
    has_architectural_details_keywords: bool = False
    has_luxury_keywords: bool = False
    has_designer_keywords: bool = False
    has_tech_ready_keywords: bool = False

    # Deal indicators
    is_price_reduced: bool = False
    is_back_on_market: bool = False

    # Red flags
    has_busy_street_keywords: bool = False
    is_north_facing_only: bool = False
    is_basement_unit: bool = False

    # Scores
    walk_score: Optional[int] = None
    transit_score: Optional[int] = None

    # Sherlock Homes Intelligence
    tranquility_score: Optional[int] = None
    tranquility_factors: Optional[Dict[str, Any]] = None
    light_potential_score: Optional[int] = None
    light_potential_signals: Optional[List[str]] = None

    # Visual Quality Intelligence (from Claude Vision photo analysis)
    visual_quality_score: Optional[int] = None
    visual_assessment: Optional[Dict[str, Any]] = None
    photos_hash: Optional[str] = None
    visual_analyzed_at: Optional[datetime] = None

    photos: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


class PropertyListingCreate(PropertyListingBase):
    pass


class PropertyListing(PropertyListingBase):
    id: int
    last_updated: Optional[datetime] = None

    # Match data (computed at query time)
    match_score: Optional[float] = None
    match_narrative: Optional[str] = None
    feature_scores: Optional[Dict[str, Any]] = None
    match_reasons: Optional[List[str]] = None
    match_tradeoff: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
