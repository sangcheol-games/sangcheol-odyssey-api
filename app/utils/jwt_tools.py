from __future__ import annotations
from datetime import UTC, datetime
from typing import Any
from authlib.jose import jwt
from app.core.config import settings
from app.schemas.jwt import JwtTokenPayload

def issue_access_token(sub: str) -> str:
    now = int(datetime.now(UTC).timestamp())
    exp = now + int(settings.JWT_EXPIRES_SEC)
    payload: dict[str, Any] = JwtTokenPayload(
        sub=sub,
        typ="access",
        iat=now,
        exp=exp,
        iss="sangcheol-odyssey",
        aud=None,
    ).model_dump(exclude_none=True)
    token = jwt.encode({"alg": "HS256", "typ": "JWT"}, payload, settings.JWT_SECRET)
    return token.decode() if isinstance(token, bytes) else token
