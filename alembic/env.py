# alembic/env.py
from __future__ import annotations

from alembic import context
from sqlalchemy import create_engine, pool

from app.core.config import settings
from app.db.base import target_metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = settings.db_url_sync
    print(f"*** ALEMBIC OFFLINE url={url}")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = settings.db_url_sync
    print(f"*** ALEMBIC ONLINE url={url}")
    connectable = create_engine(url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
