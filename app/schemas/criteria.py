from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CriteriaBase(BaseModel):
    name: Optional[str] = Field(
        default="My Criteria", description="User-friendly name for the criteria set"
    )
    is_active: Optional[bool] = Field(
        default=True, description="Is this the active criteria set for matching?"
    )

    # Quantitative
    price_min: Optional[float] = Field(default=None, description="Minimum price")
    price_max: Optional[float] = Field(
        default=None, description="Hard maximum price cap"
    )
    price_soft_max: Optional[float] = Field(
        default=None, description="Soft maximum price cap"
    )
    beds_min: Optional[int] = Field(default=None, description="Minimum bedrooms")
    baths_min: Optional[float] = Field(default=None, description="Minimum bathrooms")
    sqft_min: Optional[int] = Field(default=None, description="Minimum square footage")

    # Qualitative
    require_natural_light: Optional[bool] = Field(
        default=False, description="Require natural light keywords?"
    )
    require_high_ceilings: Optional[bool] = Field(
        default=False, description="Require high ceiling keywords?"
    )
    require_outdoor_space: Optional[bool] = Field(
        default=False, description="Require outdoor space keywords?"
    )

    # Neighborhoods
    preferred_neighborhoods: Optional[list[str]] = Field(
        default=None, description="Neighborhoods to focus on"
    )
    avoid_neighborhoods: Optional[list[str]] = Field(
        default=None, description="Neighborhoods to avoid"
    )
    neighborhood_mode: Optional[str] = Field(
        default=None, description="strict or boost"
    )

    # Recency
    max_days_on_market: Optional[int] = Field(
        default=None, description="Hard cap on days on market"
    )
    recency_mode: Optional[str] = Field(
        default=None, description="fresh, balanced, hidden_gems"
    )

    # Red flags
    avoid_busy_streets: Optional[bool] = Field(
        default=False, description="Avoid busy streets?"
    )


class CriteriaCreate(CriteriaBase):
    pass


class Criteria(CriteriaBase):
    id: int
    user_id: int
    model_config = ConfigDict(from_attributes=True)
