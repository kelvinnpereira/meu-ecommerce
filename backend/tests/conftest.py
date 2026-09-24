from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Set the database url BEFORE importing the app
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import app.database as app_db
from app.api import deps
from app.database import Base
from app.main import app

# Use an in-memory SQLite database for testing with StaticPool so all connections share the same memory
SQLALCHEMY_DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app_db.engine = engine
app_db.SessionLocal = TestingSessionLocal


# This is the dependency that will be overridden for tests
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[deps.get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Create the tables in the test database before the session starts
    Base.metadata.create_all(bind=engine)
    yield
    # Drop the tables after the test session finishes
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function", autouse=True)
def clean_db():
    """Cleans all tables after each test to guarantee total isolation."""
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Provides a fresh database session for each test."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """
    Fixture that creates a test client with the db_session fixture,
    so that tests can share the same database session.
    """

    def get_db_override():
        yield db_session

    app.dependency_overrides[deps.get_db] = get_db_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides[deps.get_db] = override_get_db
