import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure app startup doesn't run migrations or external schedulers during tests
os.environ.setdefault("RUN_DB_MIGRATIONS_ON_STARTUP", "false")
os.environ.setdefault("ZENROWS_API_KEY", "")

from app.main import app
from app.models import Base
from app.dependencies import get_db
from app.models.user import User

Path(".local").mkdir(parents=True, exist_ok=True)
SQLALCHEMY_TEST_DATABASE_URL = os.environ.get(
    "SQLALCHEMY_TEST_DATABASE_URL", "sqlite:///./.local/test.db"
)

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def test_user(db_session):
    """Ensure a test user with id=1 exists in the test DB."""
    # id=1 matches TEST_USER_ID used by the API
    user = db_session.query(User).filter(User.id == 1).first()
    if not user:
        user = User(id=1, email="test1@example.com", hashed_password="test")
        db_session.add(user)
        db_session.commit()
    return user


@pytest.fixture()
def client(db_session, test_user):
    # dependency override
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear() 
