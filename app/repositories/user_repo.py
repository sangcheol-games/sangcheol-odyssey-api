from __future__ import annotations
from uuid import UUID
from fastapi import Depends
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.session import get_session
from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return await self.db.scalar(stmt)

    async def get_by_uid(self, uid: str) -> User | None:
        stmt = select(User).where(User.uid == uid)
        return await self.db.scalar(stmt)

    async def get_all_by_nickname(self, nickname: str) -> list[User]:
        stmt = select(User).where(User.nickname == nickname)
        result = await self.db.scalars(stmt)
        return list(result)

    async def add(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user

    async def exists_uid(self, uid: str) -> bool:
        stmt = select(func.count()).select_from(User).where(User.uid == uid)
        return (await self.db.scalar(stmt)) > 0

    async def exists_nickname(self, nickname: str) -> bool:
        stmt = select(func.count()).select_from(User).where(User.nickname == nickname)
        return (await self.db.scalar(stmt)) > 0

    async def get_for_update(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id).with_for_update()
        return await self.db.scalar(stmt)

    async def update_last_login(self, user_id: UUID) -> None:
        await self.db.execute(
            text('UPDATE "user" SET last_login_at = NOW() AT TIME ZONE \'UTC\' WHERE id = :id'),
            {"id": str(user_id)},
        )

    async def list_by_uids(self, uids: list[str]) -> list[User]:
        if not uids:
            return []
        stmt = select(User).where(User.uid.in_(uids))
        res = await self.db.scalars(stmt)
        return list(res)
