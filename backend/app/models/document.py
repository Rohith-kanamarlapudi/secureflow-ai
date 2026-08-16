import uuid

from sqlalchemy import (
    Column,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Text,
    LargeBinary,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.session import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
    )

    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
    )

    filename = Column(
        String,
        nullable=False,
    )

    mime_type = Column(
        String,
    )

    is_archived = Column(
        Boolean,
        default=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
    )

    version_number = Column(
        String,
        nullable=False,
        default="1",
    )

    storage_key = Column(
        String,
        nullable=True,
    )

    nonce = Column(
        LargeBinary,
        nullable=False,
    )

    sha256_hash = Column(
        String(64),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class EncryptionKey(Base):
    __tablename__ = "encryption_keys"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    document_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("document_versions.id"),
        nullable=False,
    )

    wrapped_key = Column(
        LargeBinary,
        nullable=False,
    )

    key_version = Column(
        String,
        nullable=False,
        default="v1",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class Signature(Base):
    __tablename__ = "signatures"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    document_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("document_versions.id"),
        nullable=False,
    )

    signer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    # Base64 encoded RSA-PSS signature
    signature = Column(
        Text,
        nullable=False,
    )

    # SHA-256 hash that was signed
    hash_at_signing = Column(
        String(64),
        nullable=False,
    )

    # Base64 encoded PEM public key
    public_key = Column(
        Text,
        nullable=False,
    )

    algorithm = Column(
        String,
        nullable=False,
        default="RSA-PSS-SHA256",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
    )

    action = Column(
        String,
        nullable=False,
    )

    resource_type = Column(
        String,
        nullable=True,
    )

    resource_id = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    details = Column(
        JSONB,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )