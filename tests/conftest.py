import asyncio
import json
import os
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import sqlalchemy as sa
from fakeredis import aioredis as _fakeredis

from app.main import app
from app.core import config as cfg
from app.utils.redis_client import get_redis as _get_redis

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def _patch_settings(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("JWT_EXPIRES_SEC", "3600")
    monkeypatch.setenv("REFRESH_EXPIRES_SEC", "2592000")
    monkeypatch.setenv("REFRESH_HASH_PEPPER", "pepper")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("GOOGLE_CLIENT_ID_WEB", "cid")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost:5000/v1/auth/google/callback")
    monkeypatch.setenv("GOOGLE_CLIENT_IDS", "cid")
    from app.core import config as _cfg
    _cfg.settings = _cfg.Settings()

@pytest_asyncio.fixture
async def fake_redis():
    r = _fakeredis.FakeRedis(decode_responses=True)
    try:
        await r.flushall()
        yield r
    finally:
        try:
            await r.aclose()
        except Exception:
            pass

@pytest.fixture(autouse=True)
def _override_redis(fake_redis, monkeypatch):
    import app.utils.redis_client as rc
    app.dependency_overrides[rc.get_redis] = lambda: fake_redis
    rc._redis = fake_redis
    import app.services.auth_service as auth_service
    monkeypatch.setattr(auth_service, "redis_from_url", lambda *a, **k: fake_redis)

@pytest_asyncio.fixture
async def client(_override_redis, event_loop):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c

@pytest.fixture(scope="session")
def test_db_url():
    return cfg.settings.db_url_async

@pytest_asyncio.fixture
async def async_session():
    engine = create_async_engine(
        cfg.settings.db_url_async,
        pool_pre_ping=True,
        pool_recycle=1800,
        json_serializer=lambda o: json.dumps(o),
    )
    async with engine.begin() as conn:
        await conn.execute(sa.text('TRUNCATE TABLE "identity","user" RESTART IDENTITY CASCADE'))
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
    await engine.dispose()
