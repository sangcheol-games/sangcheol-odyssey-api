from __future__ import annotations
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.jose import jwt as jose_jwt

from app.core.config import settings
from app.core.session import get_session
from app.services.user_service import UserService

bearer = HTTPBearer(auto_error=True)

def _decode(token: str) -> dict:
    try:
        return jose_jwt.decode(token, settings.JWT_SECRET)
    except Exception:
        raise HTTPException(status_code=401, detail="invalid token")

async def get_current_user_id(
    cred: HTTPAuthorizationCredentials = Depends(bearer),
) -> str:
    claims = _decode(cred.credentials)
    sub = claims.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="invalid token (no sub)")
    return sub

async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    svc = UserService(db)
    return await svc.require_user(user_id)
