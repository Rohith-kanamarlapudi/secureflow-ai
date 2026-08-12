import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal, get_db
from app.models.user import User
from app.models.user import Organization
from app.core.security import hash_password


@pytest.fixture
def db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def seeded_user(db):
    organization = Organization(
        name=f"Test Organization {uuid.uuid4().hex[:8]}"
    )

    db.add(organization)
    db.commit()
    db.refresh(organization)

    user = User(
        email=f"test-{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("correct-pw"),
        organization_id=organization.id,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    yield user

    db.delete(user)
    db.commit()

    db.delete(organization)
    db.commit()