from __future__ import annotations
import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Set the database url BEFORE importing the app
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.api import deps
from app.database import Base
from app.main import app

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Fixture that creates a new database session with a transaction for each test case.
    The transaction is rolled back after the test, ensuring test isolation.
    """
    connection = engine.connect()
    transaction = connection.begin()
    db = Session(bind=connection)
    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()


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
    # remove dependency override after test
    app.dependency_overrides.pop(deps.get_db)
