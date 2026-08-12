import uuid

from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text, func
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
    )

    version_number = Column(
        String,
        nullable=False,
    )

    # Filled during Week 2 storage implementation
    storage_key = Column(
        String,
        nullable=True,
    )

    # Filled during Week 2 integrity implementation
    sha256_hash = Column(
        String,
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

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
    )

    key_name = Column(
        String,
        nullable=False,
    )

    encrypted_key = Column(
        Text,
        nullable=True,
    )

    algorithm = Column(
        String,
        nullable=True,
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
    )

    signer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
    )

    signature = Column(
        Text,
        nullable=True,
    )

    algorithm = Column(
        String,
        nullable=True,
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