import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

@pytest.mark.asyncio
async def test_database_created(test_db_url):
    engine = create_async_engine(test_db_url)
    async with engine.connect() as conn:
        res = await conn.execute(sa.text("select 1"))
        assert res.scalar() == 1
