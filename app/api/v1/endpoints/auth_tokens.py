from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.session import get_session
from app.deps.auth import get_current_user_id
from app.services.auth_service import rotate_refresh_and_issue, logout_all_refresh

router = APIRouter(prefix="/auth", tags=["auth"])

class RefreshBody(BaseModel):
    refresh_token: str

@router.post("/refresh")
async def refresh(body: RefreshBody, db: AsyncSession = Depends(get_session)):
    return await rotate_refresh_and_issue(db, body.refresh_token)

@router.post("/logout")
async def logout(user_id: str = Depends(get_current_user_id)):
    return await logout_all_refresh(user_id)
