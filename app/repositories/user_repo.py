from __future__ import annotations
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
