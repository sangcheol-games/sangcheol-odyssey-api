from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class TimestampedMixin(BaseModel):
    created_at: datetime = Field(...)
    updated_at: datetime | None = Field(None)

    model_config = ConfigDict(from_attributes=True)
