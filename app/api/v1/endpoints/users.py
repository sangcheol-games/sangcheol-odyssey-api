from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.session import get_session
from app.deps.auth import get_current_user, get_current_user_id
from app.schemas.user import UserOut
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserOut)
async def me(user = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)

class NicknameBody(BaseModel):
    nickname: str

@router.patch("/me/nickname", response_model=UserOut)
async def set_nickname(
    body: NicknameBody,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    svc = UserService(db)
    user = await svc.update_nickname_once(user_id, body.nickname)
    return UserOut.model_validate(user)
