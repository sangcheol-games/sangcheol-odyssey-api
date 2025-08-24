from __future__ import annotations
import json
from collections.abc import AsyncGenerator
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from app.core.config import settings


def _json_serializer(obj: Any) -> str:
    return json.dumps(jsonable_encoder(obj))


engine = create_async_engine(
    settings.db_url_async,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=getattr(settings, "DB_POOL_SIZE", None) or 5,
    max_overflow=getattr(settings, "DB_MAX_OVERFLOW", None) or 10,
    json_serializer=_json_serializer,
    connect_args={
        "server_settings": {
            "application_name": "sangcheol-odyssey-api",
            "timezone": "UTC",
            "statement_timeout": "60000",
        }
    },
)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
