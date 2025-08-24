from __future__ import annotations
import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.jose import JsonWebToken, JsonWebKey

from app.schemas.google_oauth import GoogleTokenRequest, GoogleTokenResponse, GoogleIdClaims
from app.schemas.auth_io import TokenResponse
from app.models.identity import Provider
from app.core.config import settings
from app.utils.jwks_cache import JWKSCache
from app.utils.jwt_tools import issue_access_token
from app.services.user_service import UserService

from app.utils.redis_client import get_redis
from app.utils.refresh_tools import (
    generate_refresh_plain, hash_refresh,
    redis_token_key, redis_user_set_key,
    now_ts, exp_ts, to_json, from_json,
)

GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_JWKS_URI = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISS = {"https://accounts.google.com", "accounts.google.com"}

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
    svc = UserService(db)
    user, is_new_user = await svc.create_or_get_social_user(
        provider=Provider.google,
        provider_sub=claims.sub,
        claims=claims.model_dump(exclude_none=True),
    )
    user_id = str(user.id)

    access_token = issue_access_token(user_id)

    r = get_redis()
    plain = generate_refresh_plain()
    h = hash_refresh(plain)
    key = redis_token_key(h)
    record = {"user_id": user_id, "iat": now_ts(), "exp": exp_ts()}
    await r.setex(key, int(settings.REFRESH_EXPIRES_SEC), to_json(record))
    await r.sadd(redis_user_set_key(user_id), h)

    await db.commit()
    return TokenResponse(
        access_token=access_token,
        refresh_token=plain,
        expires_in=int(settings.JWT_EXPIRES_SEC),
        is_new_user=is_new_user,
    )

async def rotate_refresh_and_issue(db: AsyncSession, refresh_plain: str) -> TokenResponse:
    if not refresh_plain:
        raise HTTPException(status_code=400, detail="missing refresh_token")

    r = get_redis()
    h = hash_refresh(refresh_plain)
    key = redis_token_key(h)

    record_json = await r.getdel(key)
    if not record_json:
        raise HTTPException(status_code=401, detail="invalid or used refresh_token")

    rec = from_json(record_json)
    user_id = rec["user_id"]

    await r.srem(redis_user_set_key(user_id), h)

    access = issue_access_token(user_id)

    new_plain = generate_refresh_plain()
    new_h = hash_refresh(new_plain)
    new_key = redis_token_key(new_h)
    new_rec = {"user_id": user_id, "iat": now_ts(), "exp": exp_ts()}
    await r.setex(new_key, int(settings.REFRESH_EXPIRES_SEC), to_json(new_rec))
    await r.sadd(redis_user_set_key(user_id), new_h)

    await db.commit()
    return TokenResponse(
        access_token=access,
        refresh_token=new_plain,
        expires_in=int(settings.JWT_EXPIRES_SEC),
        is_new_user=False,
    )

async def logout_all_refresh(user_id: str) -> dict:
    r = get_redis()
    set_key = redis_user_set_key(user_id)
    hashes = await r.smembers(set_key)
    if hashes:
        pipe = r.pipeline()
        for h in hashes:
            pipe.delete(redis_token_key(h))
        pipe.delete(set_key)
        await pipe.execute()
    return {"message": "ok"}
