from __future__ import annotations
from typing import Optional
from sqlalchemy import UUID, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import Identity


class IdentityRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_provider_sub(self, provider: str, provider_sub: str) -> Optional[Identity]:
        stmt = select(Identity).where(
            Identity.provider == provider,
            Identity.provider_sub == provider_sub,
        )
        return await self.db.scalar(stmt)

    async def get_all_by_user(self, user_id: UUID) -> list[Identity]:
        stmt = select(Identity).where(Identity.user_id == user_id)
        result = await self.db.scalars(stmt)
        return list(result)

    async def add(self, identity: Identity) -> Identity:
        self.db.add(identity)
        await self.db.flush()
        return identity
