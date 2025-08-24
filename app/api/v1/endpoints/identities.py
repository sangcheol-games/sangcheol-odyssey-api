from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Literal

from app.core.session import get_session
from app.deps.auth import get_current_user_id
from app.models.identity import Provider
from app.services.user_service import UserService

router = APIRouter(prefix="/identities", tags=["auth"])

class LinkBody(BaseModel):
    provider_sub: str
    claims: dict | None = None

@router.post("/{provider}")
async def link_identity(
    provider: Provider,
    body: LinkBody,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    svc = UserService(db)
    ident = await svc.link_identity(user_id, provider, body.provider_sub, body.claims)
    return {"id": str(ident.id), "provider": ident.provider, "provider_sub": ident.provider_sub}

class DeleteIdentityResponse(BaseModel):
    deleted: bool
    provider: Literal["google", "steam"]
    provider_sub: str | None = None
    message: str = "ok"

@router.delete("/{provider}", response_model=DeleteIdentityResponse)
async def unlink_identity(
    provider: Provider,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    svc = UserService(db)
    deleted, rows = await svc.ids.delete_returning(user_id, provider.value)
    await db.commit()
    return DeleteIdentityResponse(
        deleted=deleted > 0,
        provider=provider.value,
        provider_sub=rows[0]["provider_sub"] if rows else None,
        message="ok" if deleted else "not found or already deleted",
    )
