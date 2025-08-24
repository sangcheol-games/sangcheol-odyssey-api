from __future__ import annotations
import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.jose import JsonWebToken, JsonWebKey

from app.schemas.google_oauth import GoogleTokenRequest, GoogleTokenResponse, GoogleIdClaims
from app.schemas.auth_io import TokenResponse
from app.repositories.user_repo import UserRepository
from app.repositories.identity_repo import IdentityRepository
from app.models.user import User
from app.models.identity import Identity, Provider
from app.core.config import settings
from app.utils.jwks_cache import JWKSCache
from app.utils.jwt_tools import issue_access_token

GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_JWKS_URI = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISS = {"https://accounts.google.com", "accounts.google.com"}
_rs256 = JsonWebToken(["RS256"])

_jwks_cache = JWKSCache(GOOGLE_JWKS_URI)
_rs256 = JsonWebToken(["RS256"])

async def exchange_google_token(req: GoogleTokenRequest) -> GoogleTokenResponse:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(GOOGLE_TOKEN_ENDPOINT, data=req.to_form())
    if r.status_code != 200:
        raise HTTPException(status_code=400, detail="google token exchange failed")
    return GoogleTokenResponse.model_validate(r.json())


async def verify_google_id_token(id_token: str) -> GoogleIdClaims:
    jwks = await _jwks_cache.get()
    if not isinstance(jwks, dict) or "keys" not in jwks:
        raise HTTPException(status_code=503, detail="JWKS not available")
    keyset = JsonWebKey.import_key_set(jwks)

    audiences = settings.google_client_id_list
    if not audiences:
        raise HTTPException(status_code=500, detail="SERVER_MISCONFIG: GOOGLE_CLIENT_IDS is empty")

    claims = _rs256.decode(
        id_token,
        keyset,
        claims_options={
            "iss": {"values": list(GOOGLE_ISS)},
            "aud": {"values": audiences},
            "exp": {"essential": True},
            "iat": {"essential": True},
        },
    )
    try:
        claims.validate(leeway=10)
    except Exception as e:
        aud_in_token = claims.get("aud")
        raise HTTPException(
            status_code=400,
            detail=f"INVALID_AUDIENCE: token aud={aud_in_token}, allowed={audiences}"
        ) from e

    return GoogleIdClaims.model_validate(claims)

async def handle_google_login(db: AsyncSession, claims: GoogleIdClaims) -> TokenResponse:
    if not claims.sub:
        raise HTTPException(status_code=400, detail="id_token missing sub")
    id_repo = IdentityRepository(db)
    user_repo = UserRepository(db)
    identity = await id_repo.get_by_provider_sub(Provider.google.value, claims.sub)
    if identity:
        user = await user_repo.get(identity.user_id)
        if not user:
            raise HTTPException(status_code=400, detail="user not found for identity")
        is_new_user = False
    else:
        user = User(uid=f"google:{claims.sub}", nickname=None)
        await user_repo.add(user)
        identity = Identity(
            user_id=user.id,
            provider=Provider.google.value,
            provider_sub=claims.sub,
            email=claims.email,
            email_verified=claims.email_verified,
            profile_json=claims.model_dump(exclude_none=True),
        )
        await id_repo.add(identity)
        is_new_user = True
    await db.commit()
    access_token = issue_access_token(str(user.id))
    return TokenResponse(
        access_token=access_token,
        refresh_token=None,
        expires_in=int(settings.JWT_EXPIRES_SEC),
        is_new_user=is_new_user,
    )
