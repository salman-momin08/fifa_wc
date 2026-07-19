"""
Shared pytest fixtures for the FIFA WC 2026 Stadium Operations test suite.

Provides:
- An isolated in-memory SQLite test database (separate from production).
- A pre-seeded TestClient fixture.
- JWT token fixtures for organizer and volunteer roles.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db, init_db

# ── Isolated In-Memory Test Database ─────────────────────────────────────────
TEST_DATABASE_URL = "sqlite:///./test_stadium.db"

test_engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Dependency override: provides a test-scoped DB session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply DB override at module level
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Session-scoped fixture: creates all tables once and seeds initial data."""
    Base.metadata.create_all(bind=test_engine)
    # Seed default users via init_db (uses the overridden DB)
    db = TestingSessionLocal()
    try:
        init_db()
    finally:
        db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="session")
def test_client(setup_test_db) -> TestClient:
    """Session-scoped FastAPI test client."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def organizer_token(test_client: TestClient) -> str:
    """Issue a valid organizer JWT access token."""
    response = test_client.post(
        "/api/auth/token",
        data={"username": "organizer", "password": "organizerpassword"},
    )
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def volunteer_token(test_client: TestClient) -> str:
    """Issue a valid volunteer JWT access token."""
    response = test_client.post(
        "/api/auth/token",
        data={"username": "volunteer", "password": "volunteerpassword"},
    )
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def db_session():
    """Provide a direct DB session for unit-level service tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
