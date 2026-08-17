import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal, get_db
from app.models.user import User, Organization
from app.models.rbac import Role, user_roles
from app.models.share import DocumentShare
from app.models.document import Document
from app.core.security import hash_password
from app.core.tokens import create_access_token


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
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    yield user

    db.delete(user)
    db.commit()

    db.delete(organization)
    db.commit()


@pytest.fixture
def viewer_token(db):
    viewer_role = (
        db.query(Role)
        .filter_by(name="viewer")
        .first()
    )

    if not viewer_role:
        raise RuntimeError(
            "Viewer role not found. Run: python -m scripts.seed"
        )

    organization = Organization(
        name=f"Viewer Test Organization {uuid.uuid4().hex[:8]}"
    )

    db.add(organization)
    db.flush()

    viewer = User(
        email=f"viewer-{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("viewer-pw"),
        organization_id=organization.id,
        is_active=True,
    )

    db.add(viewer)
    db.flush()

    db.execute(
        user_roles.insert().values(
            user_id=viewer.id,
            role_id=viewer_role.id,
        )
    )

    db.commit()
    db.refresh(viewer)

    token = create_access_token(str(viewer.id))

    yield token

    db.execute(
        user_roles.delete().where(
            user_roles.c.user_id == viewer.id
        )
    )
    db.commit()

    db.delete(viewer)
    db.commit()

    db.delete(organization)
    db.commit()


@pytest.fixture
def seeded_document(db, seeded_user):
    document = Document(
        organization_id=seeded_user.organization_id,
        owner_id=seeded_user.id,
        filename="test-document.txt",
        mime_type="text/plain",
        is_archived=False,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    yield document

    db.delete(document)
    db.commit()