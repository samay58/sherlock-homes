"""API routes for Scout management."""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.dependencies import get_db
from app.models.scout import Scout, ScoutRun
from app.services.scout import ScoutService
from app.services.criteria import TEST_USER_ID

router = APIRouter(
    prefix="/scouts",
    tags=["scouts"]
)


# Pydantic schemas
class ScoutCreate(BaseModel):
    name: str
    description: str
    criteria_id: Optional[int] = None
    alert_frequency: str = "daily"
    min_match_score: float = 60.0
    max_results_per_alert: int = 10
    alert_email: bool = True
    alert_sms: bool = False
    alert_webhook: Optional[str] = None


class ScoutResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    alert_frequency: str
    min_match_score: float
    last_run: Optional[datetime]
    total_matches_found: int
    total_alerts_sent: int
    
    class Config:
        from_attributes = True


class ScoutRunResponse(BaseModel):
    id: int
    scout_id: int
    started_at: datetime
    completed_at: Optional[datetime]
    status: str
    matches_found: int
    new_matches: int
    top_score: Optional[float]
    average_score: Optional[float]
    
    class Config:
        from_attributes = True


class ScoutFeedback(BaseModel):
    listing_id: str
    is_positive: bool


@router.post("/", response_model=ScoutResponse)
def create_scout(scout_data: ScoutCreate, 
                db: Session = Depends(get_db)):
    """Create a new scout configuration."""
    # TODO: Get user_id from authenticated user
    user_id = TEST_USER_ID  # Using test user for now
    
    service = ScoutService(db)
    scout = service.create_scout(
        user_id=user_id,
        name=scout_data.name,
        description=scout_data.description,
        criteria_id=scout_data.criteria_id,
        alert_frequency=scout_data.alert_frequency,
        min_match_score=scout_data.min_match_score,
        max_results_per_alert=scout_data.max_results_per_alert,
        alert_email=scout_data.alert_email,
        alert_sms=scout_data.alert_sms,
        alert_webhook=scout_data.alert_webhook
    )
    
    return scout


@router.post("/from-description", response_model=ScoutResponse)
def create_scout_from_description(name: str, 
                                 description: str,
                                 db: Session = Depends(get_db)):
    """
    Create a scout from natural language description.
    The system will parse the description to auto-generate criteria.
    """
    # TODO: Get user_id from authenticated user
    user_id = TEST_USER_ID
    
    service = ScoutService(db)
    scout = service.create_scout_from_description(
        user_id=user_id,
        name=name,
        description=description
    )
    
    return scout


@router.get("/", response_model=List[ScoutResponse])
def list_scouts(db: Session = Depends(get_db)):
    """List all scouts for the current user."""
    # TODO: Get user_id from authenticated user
    user_id = TEST_USER_ID
    
    scouts = db.query(Scout).filter(Scout.user_id == user_id).all()
    return scouts


@router.get("/{scout_id}", response_model=ScoutResponse)
def get_scout(scout_id: int, db: Session = Depends(get_db)):
    """Get details of a specific scout."""
    # TODO: Verify user owns this scout
    scout = db.query(Scout).filter(Scout.id == scout_id).first()
    if not scout:
        raise HTTPException(status_code=404, detail="Scout not found")
    return scout


@router.post("/{scout_id}/run")
async def run_scout(scout_id: int, 
                   background_tasks: BackgroundTasks,
                   db: Session = Depends(get_db)):
    """Manually trigger a scout run."""
    # TODO: Verify user owns this scout
    scout = db.query(Scout).filter(Scout.id == scout_id).first()
    if not scout:
        raise HTTPException(status_code=404, detail="Scout not found")
    
    service = ScoutService(db)
    
    # Run scout in background
    background_tasks.add_task(service.run_scout, scout_id)
    
    return {"message": f"Scout run initiated for '{scout.name}'", "scout_id": scout_id}


@router.get("/{scout_id}/runs", response_model=List[ScoutRunResponse])
def get_scout_runs(scout_id: int, 
                  limit: int = 10,
                  db: Session = Depends(get_db)):
    """Get recent runs for a scout."""
    runs = db.query(ScoutRun).filter(
        ScoutRun.scout_id == scout_id
    ).order_by(ScoutRun.started_at.desc()).limit(limit).all()
    
    return runs


@router.get("/{scout_id}/matches")
def get_scout_matches(scout_id: int, db: Session = Depends(get_db)):
    """Get the latest matches from a scout's most recent run."""
    latest_run = db.query(ScoutRun).filter(
        ScoutRun.scout_id == scout_id,
        ScoutRun.status == "completed"
    ).order_by(ScoutRun.started_at.desc()).first()
    
    if not latest_run:
        return {"matches": [], "message": "No completed runs found"}
    
    return {
        "run_id": latest_run.id,
        "run_date": latest_run.completed_at,
        "matches": latest_run.matched_listings or [],
        "top_score": latest_run.top_score,
        "average_score": latest_run.average_score
    }


@router.post("/{scout_id}/feedback")
def submit_feedback(scout_id: int,
                   feedback: ScoutFeedback,
                   db: Session = Depends(get_db)):
    """Submit feedback on a listing to help the scout learn."""
    service = ScoutService(db)
    service.record_feedback(scout_id, feedback.listing_id, feedback.is_positive)
    
    return {"message": "Feedback recorded successfully"}


@router.patch("/{scout_id}/activate")
def activate_scout(scout_id: int, db: Session = Depends(get_db)):
    """Activate a scout."""
    scout = db.query(Scout).filter(Scout.id == scout_id).first()
    if not scout:
        raise HTTPException(status_code=404, detail="Scout not found")
    
    scout.is_active = True
    db.commit()
    
    return {"message": f"Scout '{scout.name}' activated"}


@router.patch("/{scout_id}/deactivate")
def deactivate_scout(scout_id: int, db: Session = Depends(get_db)):
    """Deactivate a scout."""
    scout = db.query(Scout).filter(Scout.id == scout_id).first()
    if not scout:
        raise HTTPException(status_code=404, detail="Scout not found")
    
    scout.is_active = False
    db.commit()
    
    return {"message": f"Scout '{scout.name}' deactivated"}


@router.delete("/{scout_id}")
def delete_scout(scout_id: int, db: Session = Depends(get_db)):
    """Delete a scout and its runs."""
    scout = db.query(Scout).filter(Scout.id == scout_id).first()
    if not scout:
        raise HTTPException(status_code=404, detail="Scout not found")
    name = scout.name
    db.delete(scout)
    db.commit()
    return {"message": f"Scout '{name}' deleted", "scout_id": scout_id}
def delete_scout(scout_id: int, db: Session = Depends(get_db)):
    """Delete a scout and all its runs."""
    scout = db.query(Scout).filter(Scout.id == scout_id).first()
    if not scout:
        raise HTTPException(status_code=404, detail="Scout not found")
    
    name = scout.name
    db.delete(scout)
    db.commit()
    
    return {"message": f"Scout '{name}' deleted successfully"}
