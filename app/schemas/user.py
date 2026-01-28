from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# Weight learning schemas


class LearnedWeightInfo(BaseModel):
    """Info about a learned weight for a criterion."""

    multiplier: float
    signal_count: int
    last_updated: str


class UserWeightsResponse(BaseModel):
    """Response for GET /users/{id}/weights."""

    user_id: int
    base_weights: Dict[str, float]
    learned_multipliers: Dict[str, float]
    effective_weights: Dict[str, float]
    signal_counts: Dict[str, int]
    total_signals: int


class PreferenceChange(BaseModel):
    """A single preference that was strengthened or weakened."""

    criterion: str
    boost_percent: Optional[int] = None
    reduction_percent: Optional[int] = None
    signals: int


class WeightLearningSummary(BaseModel):
    """Human-readable summary of learned preferences."""

    user_id: int
    total_signals: int
    preferences_learned: int
    strengthened_preferences: List[PreferenceChange]
    weakened_preferences: List[PreferenceChange]
    insight: str


class WeightRecalculationResult(BaseModel):
    """Response for POST /users/{id}/weights/recalculate."""

    weights_updated: bool
    message: str
    total_likes: int
    total_dislikes: int
    criteria_adjusted: List[str]


class WeightResetResponse(BaseModel):
    """Response for DELETE /users/{id}/weights."""

    success: bool
    message: str
