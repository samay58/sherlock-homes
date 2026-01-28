from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Detect SQLite vs PostgreSQL
database_url = str(settings.DATABASE_URL)
is_sqlite = database_url.startswith("sqlite")

# SQLite needs check_same_thread=False for FastAPI's async nature
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(database_url, echo=False, connect_args=connect_args)

# Enable foreign key enforcement for SQLite (disabled by default)
if is_sqlite:

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
