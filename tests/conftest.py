import psycopg
import pytest
from alembic.config import Config
from alembic import command
from app.core.config import settings

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
    db_name, sync_url, _, admin_url = _urls()
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
