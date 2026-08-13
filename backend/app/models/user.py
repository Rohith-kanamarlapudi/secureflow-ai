import uuid

from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.rbac import user_roles


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name = Column(
        String,
        unique=True,
        nullable=False,
    )

    users = relationship(
        "User",
        back_populates="organization",
    )


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False,
    )

    email = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    hashed_password = Column(
        String,
        nullable=False,
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    organization = relationship(
        "Organization",
        back_populates="users",
    )

    roles = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
    )