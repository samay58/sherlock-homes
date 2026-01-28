import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal, engine
from app.dependencies import get_db
from app.models import Base
from app.models.user import User
from app.routes.admin import router as admin_router
from app.routes.criteria import router as criteria_router
from app.routes.feedback import router as feedback_router
from app.routes.listings import router as listings_router
from app.routes.scouts import router as scouts_router
from app.routes.users import router as users_router
from app.services.criteria import TEST_USER_ID
from app.services.ingestion import run_ingestion_job_sync

logger = logging.getLogger(__name__)

app = FastAPI(title="Sherlock Homes API", version="0.1.0")

# --- CORS Middleware ---
# origins = [ ... ] # Keep list for later reference

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow ALL origins for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(criteria_router)
app.include_router(admin_router)
app.include_router(listings_router)
app.include_router(scouts_router)
app.include_router(feedback_router)
app.include_router(users_router)

scheduler: BackgroundScheduler | None = None


@app.on_event("startup")
def initial_setup():
    """Setup database and test user on startup."""
    database_url = str(settings.DATABASE_URL)
    is_sqlite = database_url.startswith("sqlite")

    # --- Database Setup ---
    if is_sqlite:
        # SQLite: Auto-create tables from models (replaces Alembic)
        logger.info("SQLite detected - creating tables from models...")
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully")
    else:
        # PostgreSQL: Use Alembic migrations (existing behavior)
        if settings.RUN_DB_MIGRATIONS_ON_STARTUP:
            try:
                from alembic import command as alembic_command
                from alembic.config import Config as AlembicConfig

                alembic_ini_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), "alembic.ini"
                )
                alembic_ini_path = os.path.abspath(alembic_ini_path)
                cfg = AlembicConfig(alembic_ini_path)
                cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
                alembic_command.upgrade(cfg, "head")
                logger.info("Database migrations applied/up-to-date.")
            except Exception as e:
                logger.error(
                    f"Error applying migrations at startup: {e}", exc_info=True
                )
        else:
            logger.info(
                "RUN_DB_MIGRATIONS_ON_STARTUP is false; skipping DB migrations."
            )

    # --- Ensure Test User Exists ---
    logger.info("Running startup: Ensuring test user exists...")
    db: Session = SessionLocal()
    try:
        test_user = db.query(User).filter(User.id == TEST_USER_ID).first()
        if not test_user:
            logger.warning(f"Test user {TEST_USER_ID} not found, creating...")
            hashed_pw = get_password_hash("testpassword")
            test_user = User(
                id=TEST_USER_ID,
                email=f"test{TEST_USER_ID}@example.com",
                hashed_password=hashed_pw,
            )
            db.add(test_user)
            db.commit()
            logger.info(f"Test user {TEST_USER_ID} created.")
        else:
            logger.info(f"Test user {TEST_USER_ID} already exists.")
    except Exception as e:
        logger.error(f"Database error during startup user check: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

    # ---> Start Scheduler <---
    global scheduler
    if os.getenv("ZENROWS_API_KEY") and settings.ENABLE_AUTO_INGESTION:
        scheduler = BackgroundScheduler(timezone="UTC")
        scheduler.add_job(
            run_ingestion_job_sync,
            "interval",
            hours=settings.INGESTION_INTERVAL_HOURS,
            id="ingestion_sync_job",
            replace_existing=True,
        )
        logger.info(
            f"Scheduled ingestion job to run every {settings.INGESTION_INTERVAL_HOURS} hours."
        )
        scheduler.start()
    else:
        if not os.getenv("ZENROWS_API_KEY"):
            logger.warning(
                "ZENROWS_API_KEY not set; skipping ingestion scheduler setup."
            )
        else:
            logger.info(
                "Automatic ingestion is disabled via ENABLE_AUTO_INGESTION setting."
            )


@app.on_event("shutdown")
def shutdown_scheduler():
    if scheduler:
        scheduler.shutdown()


@app.get("/ping", tags=["health"])
async def ping():
    """Simple health-check endpoint used by Docker compose and uptime monitors."""
    return {"status": "ok"}
