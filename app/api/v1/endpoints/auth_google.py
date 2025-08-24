from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.session import get_session
from app.schemas.google_oauth import GoogleTokenRequest
from app.schemas.auth_io import ExchangeRequest, VerifyIdTokenRequest, TokenResponse
from app.services.auth_service import exchange_google_token, verify_google_id_token, handle_google_login
from app.core.config import settings

router = APIRouter(prefix="/auth/google", tags=["auth"])

@router.post("/exchange", response_model=TokenResponse)
async def google_exchange(
    body: ExchangeRequest,
    db: AsyncSession = Depends(get_session),
) -> TokenResponse:
    token_resp = await exchange_google_token(
        GoogleTokenRequest(
            client_id=settings.google_client_id_list[0],
            client_secret=getattr(settings, "GOOGLE_CLIENT_SECRET", None),
            code=body.code,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
            code_verifier=body.code_verifier,
        )
    )
    if not token_resp.id_token:
        raise HTTPException(status_code=400, detail="no id_token from google")
    claims = await verify_google_id_token(token_resp.id_token)
    return await handle_google_login(db, claims)

@router.post("/verify-id-token", response_model=TokenResponse)
async def google_verify_id_token(
    body: VerifyIdTokenRequest,
    db: AsyncSession = Depends(get_session),
) -> TokenResponse:
    claims = await verify_google_id_token(body.id_token)
    return await handle_google_login(db, claims)
