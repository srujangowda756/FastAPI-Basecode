import re
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from model.enum import Role

PHONE_REGEX = re.compile(r"^\+?[0-9]{10,14}$")


class UserRegister(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.replace(" ", "").replace("-", "")
        if not PHONE_REGEX.match(v):
            raise ValueError("Invalid phone number")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower()


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    phone_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    model_config = {"extra": "forbid"}

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def name_not_null(cls, v):
        if v is None:
            raise ValueError("name cannot be null")
        return v
