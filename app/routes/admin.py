from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.services.scraper import run_scrape_job, scraper_status
from app.services.ingestion import run_ingestion_job_sync
from app.state import ingestion_state, IngestionState
from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command
from pathlib import Path
from app.core.config import settings
from fastapi import HTTPException

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/scraper/run")
def trigger_scraper():
    run_scrape_job()
    return {"detail": "scraper executed"}


@router.post("/ingestion/run")
def trigger_ingestion():
    run_ingestion_job_sync()
    return {"detail": "ingestion executed"}


@router.get("/scraper/status")
def get_status(db: Session = Depends(get_db)):
    return scraper_status(db)


@router.get("/ingestion/last-run", response_model=IngestionState)
def get_ingestion_last_run_status():
    """Returns metrics from the most recent ingestion job run."""
    return ingestion_state


def _alembic_cfg() -> AlembicConfig:
    # Resolve project root robustly, regardless of package depth
    root = Path(__file__).resolve().parents[2]  # /code
    ini = root / "alembic.ini"
    if not ini.exists():
        raise RuntimeError(f"alembic.ini not found at {ini}")
    cfg = AlembicConfig(str(ini))
    # Ensure script_location is set for safety in some environments
    cfg.set_main_option("script_location", str(root / "migrations"))
    cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    return cfg


@router.post("/migrate")
def run_migrations_now():
    """Apply Alembic migrations to head immediately."""
    try:
        cfg = _alembic_cfg()
        alembic_command.upgrade(cfg, "head")
        return {"detail": "migrations applied"}
    except Exception as e:
        # Surface error to client for easier debugging
        raise HTTPException(status_code=500, detail=f"migration failed: {e}")


@router.post("/migrate/stamp/{revision}")
def alembic_stamp(revision: str):
    """Force Alembic to record a specific revision (useful if DB has unknown revision).

    Example to align with this repo's base revision: `2eaa91ec76da`.
    """
    try:
        cfg = _alembic_cfg()
        alembic_command.stamp(cfg, revision)
        return {"detail": f"stamped to {revision}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"stamp failed: {e}")
