from __future__ import annotations
from uuid import UUID
from datetime import datetime
from pydantic import EmailStr, BaseModel
from app.schemas.timestamped_mixin import TimestampedMixin

class UserBase(BaseModel):
    email: EmailStr | None = None
    name: str | None = None

class UserCreate(UserBase):
    pass

class UserOut(UserBase, TimestampedMixin):
    id: UUID
    last_login_at: datetime | None = None
