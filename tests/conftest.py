import psycopg
import pytest
from alembic.config import Config
from alembic import command
import pytest_asyncio
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient, ASGITransport
from app.main import app


def _urls():
    base = f"{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}"
    name = settings.DB_NAME + "_test"
    return (
        name,
        f"postgresql+psycopg://{base}/{name}",
        f"postgresql+asyncpg://{base}/{name}",
        f"postgresql://{base}/postgres",
    )

def _create_db(db_name, admin_url):
    with psycopg.connect(admin_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (db_name,))
            if cur.fetchone() is None:
                cur.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
                cur.execute(f'CREATE DATABASE "{db_name}"')

def _drop_db(db_name, admin_url):
    with psycopg.connect(admin_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT pid
                FROM pg_stat_activity
                WHERE datname = %s AND pid <> pg_backend_pid()
                """,
                (db_name,),
            )
            for (pid,) in cur.fetchall():
                cur.execute("SELECT pg_terminate_backend(%s)", (pid,))
            cur.execute(f'DROP DATABASE IF EXISTS "{db_name}"')

@pytest.fixture(scope="session", autouse=True)
def _setup_db():
    db_name, sync_url, async_url, admin_url = _urls()
    _create_db(db_name, admin_url)
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", sync_url)
    command.upgrade(cfg, "head")
    yield
    _drop_db(db_name, admin_url)


@pytest.fixture()
def test_db_url():
    _, _, async_url, _ = _urls()
    return async_url

@pytest_asyncio.fixture
async def async_engine():
    _, _, async_url, _ = _urls()
    engine = create_async_engine(async_url, future=True)
    try:
        yield engine
    finally:
        await engine.dispose()

@pytest_asyncio.fixture
async def async_session(test_db_url):
    engine = create_async_engine(test_db_url)
    session_factory = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session
    await engine.dispose()

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
