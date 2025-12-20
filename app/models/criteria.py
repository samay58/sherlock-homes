from sqlalchemy import Integer, String, Float, ForeignKey, Column, Boolean, JSON, Text
from sqlalchemy.orm import relationship

from .base import Base
from .user import User


class Criteria(Base):
    """Static catalog of possible criteria (e.g., natural_light)."""

    __tablename__ = "criteria"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False, default="My Criteria")
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Quantitative Filters
    price_min = Column(Float, nullable=True)
    price_max = Column(Float, nullable=True)
    price_soft_max = Column(Float, nullable=True)
    beds_min = Column(Integer, nullable=True)
    beds_max = Column(Integer, nullable=True)
    baths_min = Column(Float, nullable=True)
    sqft_min = Column(Integer, nullable=True)
    sqft_max = Column(Integer, nullable=True)

    # Qualitative Filters (Essential Attributes)
    require_natural_light = Column(Boolean, nullable=False, default=False)
    require_high_ceilings = Column(Boolean, nullable=False, default=False)
    require_outdoor_space = Column(Boolean, nullable=False, default=False)
    require_parking = Column(Boolean, nullable=False, default=False)
    require_view = Column(Boolean, nullable=False, default=False)
    require_updated_systems = Column(Boolean, nullable=False, default=False)
    require_home_office = Column(Boolean, nullable=False, default=False)
    require_storage = Column(Boolean, nullable=False, default=False)

    # Neighborhood Preferences
    min_walk_score = Column(Integer, nullable=True)
    max_transit_distance = Column(Integer, nullable=True)  # in minutes walk
    preferred_neighborhoods = Column(JSON, nullable=True)  # list of neighborhood names
    avoid_neighborhoods = Column(JSON, nullable=True)  # list of neighborhoods to avoid
    neighborhood_mode = Column(String(20), nullable=True)  # "strict" or "boost"

    # Property Type Preferences
    property_types = Column(JSON, nullable=True)  # ["single_family", "condo", "townhouse", "loft"]
    
    # Parking Preferences
    parking_type = Column(String(50), nullable=True)  # "garage", "driveway", "street", "any"
    
    # Architectural Preferences
    min_ceiling_height = Column(Integer, nullable=True)  # in feet
    architectural_styles = Column(JSON, nullable=True)  # ["victorian", "modern", "edwardian", etc.]
    
    # Deal Preferences
    include_price_reduced = Column(Boolean, nullable=False, default=True)
    include_new_listings = Column(Boolean, nullable=False, default=True)
    max_days_on_market = Column(Integer, nullable=True)
    recency_mode = Column(String(20), nullable=True)  # "fresh", "balanced", "hidden_gems"
    
    # Red Flags (things to avoid)
    avoid_busy_streets = Column(Boolean, nullable=False, default=True)
    avoid_north_facing_only = Column(Boolean, nullable=False, default=True)
    avoid_basement_units = Column(Boolean, nullable=False, default=True)
    excluded_streets = Column(JSON, nullable=True)  # ["Van Ness", "Geary", "19th Ave"]
    
    # Scout Description
    scout_description = Column(Text, nullable=True)  # Full natural language description
    
    # Weighting for scoring
    feature_weights = Column(JSON, nullable=True)  # {"natural_light": 10, "outdoor_space": 8, etc.}

    # relationships
    user = relationship("User", back_populates="criteria", lazy="joined") 
