from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class IngestionState(BaseModel):
    """Simple in-memory storage for the last ingestion run's metrics."""
    last_run_start_time: Optional[datetime] = Field(default=None, description="UTC start time of the last run")
    last_run_end_time: Optional[datetime] = Field(default=None, description="UTC end time of the last run")
    last_run_summary_count: int = Field(default=0, description="Number of listing summaries fetched")
    last_run_detail_calls: int = Field(default=0, description="Number of detail API calls made")
    last_run_upsert_count: int = Field(default=0, description="Number of listings upserted (enriched or summary)")
    last_run_error: Optional[str] = Field(default=None, description="Error message if the last run failed catastrophically")

# Global instance to hold the state
# This is simple but won't persist across restarts or multiple workers.
# For production, consider Redis, a database table, or a file.
ingestion_state = IngestionState() 