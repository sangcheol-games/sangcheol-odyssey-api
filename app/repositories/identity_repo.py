from __future__ import annotations
from uuid import UUID

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import Identity


class IdentityRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_provider_sub(self, provider: str, provider_sub: str) -> Identity | None:
        stmt = select(Identity).where(
            Identity.provider == provider,
            Identity.provider_sub == provider_sub,
        )
        return await self.db.scalar(stmt)

    async def get_all_by_user(self, user_id: UUID) -> list[Identity]:
        stmt = select(Identity).where(Identity.user_id == user_id)
        result = await self.db.scalars(stmt)
        return list(result)

    async def get_by_user_and_provider(self, user_id: UUID, provider: str) -> Identity | None:
        stmt = select(Identity).where(
            Identity.user_id == user_id,
            Identity.provider == provider,
        )
        return await self.db.scalar(stmt)

    async def exists_provider_for_user(self, user_id: UUID, provider: str) -> bool:
        stmt = select(func.count()).select_from(Identity).where(
            Identity.user_id == user_id,
            Identity.provider == provider,
        )
        return (await self.db.scalar(stmt)) > 0

    async def delete(self, user_id: UUID, provider: str) -> int:
        stmt = delete(Identity).where(
            Identity.user_id == user_id,
            Identity.provider == provider,
        )
        res = await self.db.execute(stmt)
        return res.rowcount or 0

    async def delete_returning(self, user_id: UUID, provider: str) -> tuple[int, list[dict]]: 
        stmt = (
            delete(Identity)
            .where(Identity.user_id == user_id, Identity.provider == provider)
            .returning(Identity.provider, Identity.provider_sub)
        )
        res = await self.db.execute(stmt)
        rows = res.fetchall()
        return len(rows), [{"provider": r[0], "provider_sub": r[1]} for r in rows]

    async def add(self, identity: Identity) -> Identity:
        self.db.add(identity)
        await self.db.flush()
        return identity
