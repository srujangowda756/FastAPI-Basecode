import uuid
from datetime import datetime, timezone

from sqlalchemy import Column,String,DateTime,Boolean,Enum
from sqlalchemy.dialects.postgresql import UUID

from database import Base
from model.enum import Gender


class User(Base):
    __tablename__ = "users"

    id=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String(15), unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)

    gender = Column(Enum(Gender, name="gender_enum"), nullable=True)
    phone_verified = Column(Boolean, nullable=False, default=False)
    is_blocked = Column(Boolean, nullable=False, default=False)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(tz=timezone.utc),
    )
