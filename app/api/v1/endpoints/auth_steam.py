from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.session import get_session
from app.schemas.auth_io import TokenResponse
from app.schemas.steam_auth import SteamLoginRequest
from app.services.auth_steam import handle_steam_login

router = APIRouter(prefix="/auth/steam", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def steam_login(
    body: SteamLoginRequest,
    db: AsyncSession = Depends(get_session),
) -> TokenResponse:
    return await handle_steam_login(db, body.ticket)
