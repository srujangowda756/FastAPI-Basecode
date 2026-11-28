import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID

from database import Base
from model.enum import Role


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String(15), unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    phone_verified = Column(Boolean, nullable=False, default=False)
    is_blocked = Column(Boolean, nullable=False, default=False)
    role = Column(
        Enum(Role, name="role_enum"),
        nullable=False,
        default=Role.user,
        server_default="user",
    )
    profile_photo_id = Column(UUID(as_uuid=True), nullable=True) 

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(tz=timezone.utc),
    )
