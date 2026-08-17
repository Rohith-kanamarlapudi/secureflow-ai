from datetime import datetime, timedelta, timezone
import uuid

import pytest

from app.models.share import DocumentShare
from app.models.user import User
from app.core.security import hash_password
from app.core.tokens import create_access_token


@pytest.fixture
def other_user(db, seeded_document):
    """
    Create another user in the same organization as the
    document owner.
    """

    user = User(
        email=f"shared-{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("shared-pw"),
        organization_id=seeded_document.organization_id,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    yield user

    db.delete(user)
    db.commit()


@pytest.fixture
def other_user_token(other_user):
    """
    JWT token for the user receiving the document share.
    """

    return create_access_token(str(other_user.id))


@pytest.fixture
def expired_share(db, seeded_document, other_user):
    """
    Create a share that has already expired.
    """

    expired_time = datetime.now(timezone.utc) - timedelta(
        minutes=10
    )

    share = DocumentShare(
        document_id=seeded_document.id,
        shared_with_user_id=other_user.id,
        permission_level="view",
        expires_at=expired_time,
        revoked_at=None,
    )

    db.add(share)
    db.commit()
    db.refresh(share)

    yield share

    db.delete(share)
    db.commit()


@pytest.fixture
def revoked_share(db, seeded_document, other_user):
    """
    Create a share that has been revoked.
    """

    now = datetime.now(timezone.utc)

    share = DocumentShare(
        document_id=seeded_document.id,
        shared_with_user_id=other_user.id,
        permission_level="view",
        expires_at=now + timedelta(hours=1),
        revoked_at=now,
    )

    db.add(share)
    db.commit()
    db.refresh(share)

    yield share

    db.delete(share)
    db.commit()


def test_expired_share_rejected(
    client,
    expired_share,
    other_user_token,
):
    response = client.get(
        f"/documents/{expired_share.document_id}/download",
        headers={
            "Authorization": f"Bearer {other_user_token}"
        },
    )

    assert response.status_code == 403


def test_revoked_share_rejected(
    client,
    revoked_share,
    other_user_token,
):
    response = client.get(
        f"/documents/{revoked_share.document_id}/download",
        headers={
            "Authorization": f"Bearer {other_user_token}"
        },
    )

    assert response.status_code == 403