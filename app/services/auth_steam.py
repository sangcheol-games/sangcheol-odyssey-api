import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.identity import Provider
from app.services.user_service import UserService
from app.services.auth_service import issue_auth_tokens
from app.schemas.auth_io import TokenResponse

STEAM_AUTHENTICATE_URL = "https://api.steampowered.com/ISteamUserAuth/AuthenticateUserTicket/v1/"

async def handle_steam_login(db: AsyncSession, ticket: str) -> TokenResponse:
    if not settings.STEAM_WEB_API_KEY:
        raise HTTPException(
            status_code=500, 
            detail="SERVER_MISCONFIG: STEAM_WEB_API_KEY is missing. Please check your .env file."
        )
    
    steam_app_id = settings.STEAM_APP_ID or "4566350"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                STEAM_AUTHENTICATE_URL,
                params={
                    "key": settings.STEAM_WEB_API_KEY,
                    "appid": steam_app_id,
                    "ticket": ticket,
                }
            )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to communicate with Steam authentication servers: {e}",
        ) from e

    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Steam authentication request failed: {r.status_code}")

    try:
        data = r.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Invalid JSON response from Steam API")

    params = data.get("response", {}).get("params", {})
    if params.get("result") != "OK" or "steamid" not in params:
        error_info = data.get("response", {}).get("error", {})
        error_desc = error_info.get("errordesc") or params.get("result") or "Unknown error"
        raise HTTPException(status_code=400, detail=f"Invalid steam ticket: {error_desc}")

    steamid = str(params["steamid"])

    claims = {
        "steamid": steamid,
        "ownersteamid": str(params.get("ownersteamid")) if params.get("ownersteamid") else None,
        "vacbanned": params.get("vacbanned"),
        "publisherbanned": params.get("publisherbanned"),
    }

    svc = UserService(db)
    user, is_new_user = await svc.create_or_get_social_user(
        provider=Provider.steam,
        provider_sub=steamid,
        claims=claims
    )

    return await issue_auth_tokens(str(user.id), is_new_user)
