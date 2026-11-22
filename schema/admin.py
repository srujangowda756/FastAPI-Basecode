import uuid
from typing import Optional

from pydantic import BaseModel, Field

from model.enum import Role


class AdminAction(BaseModel):
    model_config = {"extra": "forbid"}

    reason: Optional[str] = Field(default=None, max_length=500)


class AdminUserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    phone: str
    phone_verified: bool
    is_blocked: bool
    role: Role

    model_config = {"from_attributes": True}