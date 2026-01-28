from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, Integer,
                        String, Text, UniqueConstraint)

from .base import Base


class PropertyListing(Base):
    __tablename__ = "property_listings"
    __table_args__ = (
        UniqueConstraint(
            "source", "source_listing_id", name="uq_property_listings_source_listing_id"
        ),
    )

    id = Column(Integer, primary_key=True)
    # provider-specific unique id (legacy single-source)
    listing_id = Column(String(64), unique=True, index=True, nullable=True)
    source = Column(String(32), nullable=True)
    source_listing_id = Column(String(512), nullable=True)
    sources_seen = Column(JSON, nullable=True)
    last_seen_at = Column(DateTime, nullable=True)
    address = Column(String(255), nullable=False, index=True)
    price = Column(Float, nullable=True)
    # price may be unknown for some listings
    beds = Column(Integer, nullable=True)
    baths = Column(Float, nullable=True)
    sqft = Column(Integer, nullable=True)
    property_type = Column(String(50), nullable=True)
    url = Column(String(500), nullable=False)

    # geo & metadata
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    year_built = Column(Integer, nullable=True)
    listing_status = Column(String(20), nullable=True)

    description = Column(Text, nullable=True)

    status = Column(String(20), default="active")
    days_on_market = Column(Integer, nullable=True)

    # extracted features - Essential Attributes
    has_natural_light_keywords = Column(Boolean, default=False)
    has_high_ceiling_keywords = Column(Boolean, default=False)
    has_outdoor_space_keywords = Column(Boolean, default=False)
    has_parking_keywords = Column(Boolean, default=False)
    has_view_keywords = Column(Boolean, default=False)
    has_updated_systems_keywords = Column(Boolean, default=False)
    has_home_office_keywords = Column(Boolean, default=False)
    has_storage_keywords = Column(Boolean, default=False)
    has_open_floor_plan_keywords = Column(Boolean, default=False)
    has_architectural_details_keywords = Column(Boolean, default=False)

    # Property Quality Indicators
    has_luxury_keywords = Column(Boolean, default=False)
    has_designer_keywords = Column(Boolean, default=False)
    has_tech_ready_keywords = Column(Boolean, default=False)

    # Deal Indicators
    is_price_reduced = Column(Boolean, default=False)
    price_reduction_amount = Column(Float, nullable=True)
    price_reduction_date = Column(DateTime, nullable=True)
    is_back_on_market = Column(Boolean, default=False)

    # Red Flags
    has_busy_street_keywords = Column(Boolean, default=False)
    has_foundation_issues_keywords = Column(Boolean, default=False)
    has_hoa_issues_keywords = Column(Boolean, default=False)
    is_north_facing_only = Column(Boolean, default=False)
    is_basement_unit = Column(Boolean, default=False)

    # Neighborhood Data
    neighborhood = Column(String(100), nullable=True)
    walk_score = Column(Integer, nullable=True)
    transit_score = Column(Integer, nullable=True)
    bike_score = Column(Integer, nullable=True)

    # Parking Details
    parking_type = Column(String(50), nullable=True)  # garage, driveway, street
    parking_spaces = Column(Integer, nullable=True)
    has_ev_charging = Column(Boolean, default=False)

    # HOA Information (for condos)
    hoa_fee = Column(Float, nullable=True)
    hoa_includes = Column(JSON, nullable=True)  # ["water", "garbage", "gym", etc.]

    # Additional Metadata
    lot_size = Column(Integer, nullable=True)  # in sqft
    stories = Column(Integer, nullable=True)
    architectural_style = Column(String(50), nullable=True)
    listing_agent = Column(String(100), nullable=True)
    listing_brokerage = Column(String(100), nullable=True)

    # Scoring
    match_score = Column(Float, nullable=True)  # calculated match score
    feature_scores = Column(JSON, nullable=True)  # breakdown of scores by feature

    # Sherlock Homes Intelligence (cached scores)
    tranquility_score = Column(Integer, nullable=True)  # 0-100, from geospatial
    tranquility_factors = Column(JSON, nullable=True)  # distance to noise sources
    light_potential_score = Column(Integer, nullable=True)  # 0-100, from NLP
    light_potential_signals = Column(JSON, nullable=True)  # what contributed to score

    # Visual Quality Intelligence (from Claude Vision photo analysis)
    visual_quality_score = Column(
        Integer, nullable=True
    )  # 0-100, overall visual appeal
    visual_assessment = Column(
        JSON, nullable=True
    )  # {modernity, condition, brightness, staging, cleanliness, red_flags, highlights}
    photos_hash = Column(String(64), nullable=True)  # SHA256 for cache invalidation
    visual_analyzed_at = Column(DateTime, nullable=True)

    photos = Column(JSON, nullable=True)

    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
