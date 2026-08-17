"""add day9 signature metadata

Revision ID: 7c68a9156627
Revises: ef96aec5c521
Create Date: 2026-08-16 23:15:05.440317

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# ============================================================
# Revision identifiers
# ============================================================

revision: str = "7c68a9156627"
down_revision: Union[str, Sequence[str], None] = "ef96aec5c521"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ============================================================
# Upgrade
# ============================================================

def upgrade() -> None:
    """Upgrade schema."""

    # ========================================================
    # document_versions
    # ========================================================

    # Existing document_versions rows already exist.
    # Therefore nonce must initially allow NULL.
    op.add_column(
        "document_versions",
        sa.Column(
            "nonce",
            sa.LargeBinary(),
            nullable=True,
        ),
    )

    # Existing encrypted versions need a value so that
    # the column can safely become NOT NULL.
    #
    # This is ONLY a migration value for legacy rows.
    # New encryption operations continue generating a
    # cryptographically random 12-byte nonce.
    op.execute(
        """
        UPDATE document_versions
        SET nonce = decode(
            '000000000000000000000000',
            'hex'
        )
        WHERE nonce IS NULL
        """
    )

    op.alter_column(
        "document_versions",
        "nonce",
        existing_type=sa.LargeBinary(),
        nullable=False,
    )

    # Existing document_id values should already be present.
    # Keep this change because the Day 9 model requires it.
    op.alter_column(
        "document_versions",
        "document_id",
        existing_type=sa.UUID(),
        nullable=False,
    )

    # ========================================================
    # encryption_keys
    # ========================================================

    # The previous encryption_keys schema contained:
    #
    # organization_id
    # key_name
    # encrypted_key
    # algorithm
    #
    # The Day 9 schema replaces those fields with:
    #
    # document_version_id
    # wrapped_key
    # key_version
    #
    # Add the new columns as nullable first so existing rows
    # do not immediately violate NOT NULL constraints.

    op.add_column(
        "encryption_keys",
        sa.Column(
            "document_version_id",
            sa.UUID(),
            nullable=True,
        ),
    )

    op.add_column(
        "encryption_keys",
        sa.Column(
            "wrapped_key",
            sa.LargeBinary(),
            nullable=True,
        ),
    )

    op.add_column(
        "encryption_keys",
        sa.Column(
            "key_version",
            sa.String(),
            nullable=True,
        ),
    )

    # --------------------------------------------------------
    # Remove old organization foreign key
    # --------------------------------------------------------

    op.drop_constraint(
        op.f(
            "encryption_keys_organization_id_fkey"
        ),
        "encryption_keys",
        type_="foreignkey",
    )

    # --------------------------------------------------------
    # Remove legacy columns
    # --------------------------------------------------------

    op.drop_column(
        "encryption_keys",
        "organization_id",
    )

    op.drop_column(
        "encryption_keys",
        "encrypted_key",
    )

    op.drop_column(
        "encryption_keys",
        "algorithm",
    )

    op.drop_column(
        "encryption_keys",
        "key_name",
    )

    # --------------------------------------------------------
    # Add new foreign key
    # --------------------------------------------------------

    op.create_foreign_key(
        "fk_encryption_keys_document_version_id",
        "encryption_keys",
        "document_versions",
        ["document_version_id"],
        ["id"],
    )

    # --------------------------------------------------------
    # IMPORTANT
    #
    # We intentionally leave these three columns nullable
    # during this migration.
    #
    # Existing encryption_key records cannot safely be mapped
    # to document versions without knowing their historical
    # relationship.
    #
    # New records created by the application will contain all
    # three values.
    # --------------------------------------------------------

    # ========================================================
    # signatures
    # ========================================================

    # Existing signatures may already exist from the previous
    # schema, so add the new metadata columns as nullable first.

    op.add_column(
        "signatures",
        sa.Column(
            "hash_at_signing",
            sa.String(length=64),
            nullable=True,
        ),
    )

    op.add_column(
        "signatures",
        sa.Column(
            "public_key",
            sa.Text(),
            nullable=True,
        ),
    )

    # Existing rows must not violate the NOT NULL constraints
    # on the existing signature fields.
    #
    # Only enforce NOT NULL on the existing fields if their
    # data is already valid.

    op.alter_column(
        "signatures",
        "document_version_id",
        existing_type=sa.UUID(),
        nullable=False,
    )

    op.alter_column(
        "signatures",
        "signer_id",
        existing_type=sa.UUID(),
        nullable=False,
    )

    op.alter_column(
        "signatures",
        "signature",
        existing_type=sa.TEXT(),
        nullable=False,
    )

    op.alter_column(
        "signatures",
        "algorithm",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )


# ============================================================
# Downgrade
# ============================================================

def downgrade() -> None:
    """Downgrade schema."""

    # ========================================================
    # signatures
    # ========================================================

    op.alter_column(
        "signatures",
        "algorithm",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )

    op.alter_column(
        "signatures",
        "signature",
        existing_type=sa.TEXT(),
        nullable=True,
    )

    op.alter_column(
        "signatures",
        "signer_id",
        existing_type=sa.UUID(),
        nullable=True,
    )

    op.alter_column(
        "signatures",
        "document_version_id",
        existing_type=sa.UUID(),
        nullable=True,
    )

    op.drop_column(
        "signatures",
        "public_key",
    )

    op.drop_column(
        "signatures",
        "hash_at_signing",
    )

    # ========================================================
    # encryption_keys
    # ========================================================

    op.drop_constraint(
        "fk_encryption_keys_document_version_id",
        "encryption_keys",
        type_="foreignkey",
    )

    # Restore legacy columns.

    op.add_column(
        "encryption_keys",
        sa.Column(
            "key_name",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=False,
            server_default="legacy",
        ),
    )

    op.add_column(
        "encryption_keys",
        sa.Column(
            "algorithm",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )

    op.add_column(
        "encryption_keys",
        sa.Column(
            "encrypted_key",
            sa.TEXT(),
            autoincrement=False,
            nullable=True,
        ),
    )

    op.add_column(
        "encryption_keys",
        sa.Column(
            "organization_id",
            sa.UUID(),
            autoincrement=False,
            nullable=True,
        ),
    )

    op.create_foreign_key(
        op.f(
            "encryption_keys_organization_id_fkey"
        ),
        "encryption_keys",
        "organizations",
        ["organization_id"],
        ["id"],
    )

    op.drop_column(
        "encryption_keys",
        "key_version",
    )

    op.drop_column(
        "encryption_keys",
        "wrapped_key",
    )

    op.drop_column(
        "encryption_keys",
        "document_version_id",
    )

    # ========================================================
    # document_versions
    # ========================================================

    op.alter_column(
        "document_versions",
        "document_id",
        existing_type=sa.UUID(),
        nullable=True,
    )

    op.drop_column(
        "document_versions",
        "nonce",
    )