from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class ListingEvent(BaseModel):
    id: int
    listing_id: int
    event_type: str
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ListingEventFeed(ListingEvent):
    address: Optional[str] = None
    price: Optional[float] = None
    url: Optional[str] = None
