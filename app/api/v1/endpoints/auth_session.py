from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query, Response, status, Depends
from pydantic import BaseModel
from redis.asyncio import Redis
from app.schemas.auth_io import AuthUrlResponse, TokenResponse
from app.deps.redis import get_redis
from app.utils.auth_session import create_auth_session, get_status

router = APIRouter(prefix="/auth/session", tags=["auth"])

class InitBody(BaseModel):
    code_verifier: str

@router.post("/init", response_model=AuthUrlResponse)
async def init_auth_session(body: InitBody, r: Redis = Depends(get_redis)) -> AuthUrlResponse:
    data = await create_auth_session(r, body.code_verifier)
    return AuthUrlResponse(auth_url=data["auth_url"], session_id=data["session_id"])

@router.get("/poll")
async def poll_session(sid: str = Query(...), r: Redis = Depends(get_redis)):
    status_str, result, error_msg = await get_status(r, sid)
    if status_str == "not_found":
        raise HTTPException(status_code=404, detail="session not found")
    if status_str == "ready" and result:
        return TokenResponse.model_validate(result)
    if status_str == "error":
        raise HTTPException(status_code=400, detail=error_msg or "auth failed")
    return Response(content='{"message":"pending"}', media_type="application/json", status_code=status.HTTP_202_ACCEPTED)
