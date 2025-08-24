from __future__ import annotations

import secrets
import uuid
import re
from datetime import datetime, timezone
from typing import Any, Final

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.identity import Identity, Provider
from app.repositories.user_repo import UserRepository
from app.repositories.identity_repo import IdentityRepository
from app.core.error import SCDomainError, DomainErrorCode

UID_MIN: Final[int] = 100_000_000
UID_MAX: Final[int] = 9_999_999_999
UID_RETRY_MAX: Final[int] = 10

NICKNAME_RE = re.compile(r"^[A-Za-z0-9가-힣_.-]{2,16}$")


def _gen_numeric_uid() -> str:
    span = UID_MAX - UID_MIN + 1
    n = UID_MIN + secrets.randbelow(span)
    return str(n)


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)
        self.ids = IdentityRepository(db)

    @staticmethod
    def _validate_nickname(nickname: str) -> str:
        nn = nickname.strip()
        if not NICKNAME_RE.match(nn):
            raise SCDomainError(DomainErrorCode.INVALID_NICKNAME, "Invalid nickname")
        return nn

    async def _assign_numeric_uid(self, user: User) -> None:
        if user.uid:
            return
        for _ in range(UID_RETRY_MAX):
            try_uid = _gen_numeric_uid()
            user.uid = try_uid
            try:
                await self.db.flush()
                return
            except IntegrityError:
                await self.db.rollback()
                try:
                    user.uid = None
                    await self.db.flush(objects=[user])
                except Exception:
                    pass
                continue
        raise SCDomainError(DomainErrorCode.UID_CREATE_FAILED, "Failed to create uid.")

    async def get_user(self, user_id: uuid.UUID) -> User | None:
        return await self.users.get(user_id)

    async def get_user_by_uid(self, uid: str) -> User | None:
        return await self.users.get_by_uid(uid)

    async def get_users_by_nickname(self, nickname: str) -> list[User]:
        nn = (nickname or "").strip()
        if not nn:
            raise SCDomainError(DomainErrorCode.INVALID_NICKNAME, "Invalid nickname: empty nickname.")
        return await self.users.get_all_by_nickname(nn)

    async def require_user(self, user_id: uuid.UUID) -> User:
        user = await self.users.get(user_id)
        if not user:
            raise SCDomainError(DomainErrorCode.USER_NOT_FOUND, "User not found.")
        return user

    async def require_user_by_uid(self, uid: str) -> User:
        u = (uid or "").strip()
        if not u.isdigit() or not (9 <= len(u) <= 10):
            raise SCDomainError(DomainErrorCode.INVALID_UID, "Invalid uid.")
        user = await self.users.get_by_uid(u)
        if not user:
            raise SCDomainError(DomainErrorCode.USER_NOT_FOUND, "User not found.")
        return user

    async def create_guest_user(self) -> User:
        user = User(
            uid=None,
            nickname=None,
            last_login_at=datetime.now(timezone.utc),
        )
        await self.users.add(user)
        await self.db.commit()
        return user

    async def create_or_get_social_user(
        self,
        provider: Provider,
        provider_sub: str,
        claims: dict[str, Any] | None = None,
    ) -> tuple[User, bool]:
        identity = await self.ids.get_by_provider_sub(provider.value, provider_sub)
        is_new = False
        if identity:
            user = await self.users.get(identity.user_id)
            if not user:
                raise SCDomainError(DomainErrorCode.USER_NOT_FOUND, "User not found.")
            user.last_login_at = datetime.now(timezone.utc)
        else:
            user = User(
                uid=None,
                nickname=None,
                last_login_at=datetime.now(timezone.utc),
            )
            await self.users.add(user)
            ident = Identity(
                user_id=user.id,
                provider=provider.value,
                provider_sub=provider_sub,
                email=claims.get("email") if claims else None,
                email_verified=claims.get("email_verified") if claims else None,
                profile_json=claims,
            )
            await self.ids.add(ident)
            await self._assign_numeric_uid(user)
            is_new = True

        await self.db.commit()
        return user, is_new

    async def update_nickname_once(self, user_id: uuid.UUID, nickname: str) -> User:
        user = await self.get_user(user_id)
        if user.nickname:
            raise SCDomainError(DomainErrorCode.NICKNAME_ALREADY_SET, "Nickname already set")
        nn = self._validate_nickname(nickname)
        user.nickname = nn
        await self.db.commit()
        return user
    
    async def change_nickname(self, user_id: uuid.UUID, nickname: str) -> User:
        user = await self.require_user(user_id)
        nn = self._validate_nickname(nickname)
        user.nickname = nn
        await self.db.commit()
        return user

    async def link_identity(
        self,
        user_id: uuid.UUID,
        provider: Provider,
        provider_sub: str,
        claims: dict[str, Any] | None = None,
    ) -> Identity:
        user = await self.require_user(user_id)

        existing = await self.ids.get_by_provider_sub(provider.value, provider_sub)
        if existing:
            if existing.user_id == user.id:
                raise SCDomainError(
                    DomainErrorCode.PROVIDER_ALREADY_LINKED, 
                    "This identity is already linked to the user."
                )
            raise SCDomainError(
                DomainErrorCode.IDENTITY_CONFLICT,
                "This identity is already linked to another user."
            )

        if await self.ids.exists_provider_for_user(user.id, provider.value):
            raise SCDomainError(
                DomainErrorCode.PROVIDER_ALREADY_LINKED,
                "This provider is already linked to the user."
            )

        ident = Identity(
            user_id=user.id,
            provider=provider.value,
            provider_sub=provider_sub,
            email=(claims or {}).get("email"),
            email_verified=(claims or {}).get("email_verified"),
            profile_json=claims,
        )
        try:
            await self.ids.add(ident)
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise SCDomainError(
                DomainErrorCode.INVALID_UID,
                "Failed to link identity due to a conflict."
            )

        return ident
