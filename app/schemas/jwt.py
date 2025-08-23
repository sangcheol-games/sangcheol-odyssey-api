from __future__ import annotations
from datetime import UTC, datetime
from typing import Literal
from pydantic import BaseModel, Field

class JwtTokenPayload(BaseModel):
    sub: str
    typ: Literal["access", "refresh"]
    exp: int
    iat: int = Field(default_factory=lambda: int(datetime.now(UTC).timestamp()))
    iss: str | None = None
    aud: str | None = None
