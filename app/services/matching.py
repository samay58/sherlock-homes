from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models.criteria import Criteria
from app.models.listing import PropertyListing

def find_matches(criteria: Criteria, db: Session) -> List[PropertyListing]:
    """Find property listings matching the given criteria."""
    
    query = select(PropertyListing)
    filters = []

    # --- Quantitative Filters --- 
    if criteria.price_min is not None:
        filters.append(PropertyListing.price >= criteria.price_min)
    if criteria.price_max is not None:
        filters.append(PropertyListing.price <= criteria.price_max)
    if criteria.beds_min is not None:
        filters.append(PropertyListing.beds >= criteria.beds_min)
    if criteria.baths_min is not None:
        filters.append(PropertyListing.baths >= criteria.baths_min)
    if criteria.sqft_min is not None:
        filters.append(PropertyListing.sqft >= criteria.sqft_min)
    
    # --- Qualitative Filters (Flags) ---
    if criteria.require_natural_light:
        filters.append(PropertyListing.has_natural_light_keywords == True)
    if criteria.require_high_ceilings: # Assumes model field name reflects this
        # Adjust field name if different (e.g., PropertyListing.has_high_ceiling_keywords)
        filters.append(PropertyListing.has_high_ceiling_keywords == True)
    if criteria.require_outdoor_space:
        filters.append(PropertyListing.has_outdoor_space_keywords == True)

    # TODO: Add other filters like location, property type etc. if needed

    # Apply all filters
    if filters:
        query = query.where(and_(*filters))

    # TODO: Add scoring and sorting logic later if desired
    query = query.order_by(PropertyListing.price.asc().nulls_last()) # Example sort

    results = db.scalars(query).all()
    return list(results) 