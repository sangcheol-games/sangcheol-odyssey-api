from __future__ import annotations
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.timestamped_mixin import TimestampedMixin

class UserBase(BaseModel):
    uid: str = Field(...)
    nickname: str | None = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    nickname: str | None = None

class UserOut(UserBase, TimestampedMixin):
    id: UUID
    last_login_at: datetime | None = None
