"""add document shares

Revision ID: ee2688c6a568
Revises: 7c68a9156627
Create Date: 2026-08-17 15:18:26.732190

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# ============================================================
# Revision identifiers
# ============================================================

revision: str = "ee2688c6a568"
down_revision: Union[str, Sequence[str], None] = "7c68a9156627"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ============================================================
# Upgrade
# ============================================================

def upgrade() -> None:
    """Create document shares table."""

    op.create_table(
        "document_shares",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),

        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "shared_with_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "permission_level",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
        ),

        sa.ForeignKeyConstraint(
            ["shared_with_user_id"],
            ["users.id"],
        ),
    )


# ============================================================
# Downgrade
# ============================================================

def downgrade() -> None:
    """Drop document shares table."""

    op.drop_table("document_shares")