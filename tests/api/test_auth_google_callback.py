from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from pydantic import BaseModel

from app.core.session import get_session
from app.core.config import settings
from app.utils.redis_client import get_redis
from app.utils.auth_session import (
    set_result, set_error, get_status, get_code_verifier
)
from app.schemas.google_oauth import GoogleTokenRequest
from app.schemas.auth_io import TokenResponse
from app.services import auth_service as S

router = APIRouter(prefix="/auth/google", tags=["auth"])

@router.get("/callback", response_class=HTMLResponse)
async def google_callback(
    sid: str = Query(..., alias="state"),
    code: str | None = Query(None),
    error: str | None = Query(None),
    r: Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_session),
):
    status_str, _, _ = await get_status(r, sid)
    if status_str == "not_found":
        raise HTTPException(status_code=404, detail="session not found")

    if error:
        await set_error(r, sid, f"google_error:{error}")
        return "<!doctype html><title>Auth</title>Login failed"

    if not code:
        raise HTTPException(status_code=400, detail="missing code")

    client_id = settings.GOOGLE_CLIENT_ID_WEB or (
        settings.google_client_id_list[0] if settings.google_client_id_list else None
    )
    if not client_id or not settings.GOOGLE_REDIRECT_URI:
        await set_error(r, sid, "SERVER_MISCONFIG")
        raise HTTPException(status_code=500, detail="SERVER_MISCONFIG")

    cv = await get_code_verifier(r, sid)
    if not cv:
        raise HTTPException(status_code=404, detail="session not found")

    token_resp = await S.exchange_google_token(GoogleTokenRequest(
        client_id=client_id,
        client_secret=getattr(settings, "GOOGLE_CLIENT_SECRET", None),
        code=code,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
        code_verifier=cv,
    ))

    if not token_resp.id_token:
        await set_error(r, sid, "no_id_token")
        return "<!doctype html><title>Auth</title>Login failed"

    claims = await S.verify_google_id_token(token_resp.id_token)
    tok = await S.handle_google_login(db, claims)

    if isinstance(tok, BaseModel):
        payload = tok.model_dump()
    elif isinstance(tok, dict):
        payload = tok
    else:
        payload = TokenResponse.model_validate(tok).model_dump()

    await set_result(r, sid, payload)
    return "<!doctype html><title>Auth</title>Login complete"
