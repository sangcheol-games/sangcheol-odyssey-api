import uuid
import pytest
import app.db.base_class  # noqa: F401
from app.models.user import User
from app.models.identity import Identity, Provider


@pytest.mark.asyncio
async def test_user_model_relationship(async_session):
    user = User(uid="user1", nickname="nick")
    async_session.add(user)
    await async_session.flush()
    assert isinstance(user.id, uuid.UUID)
    assert user.created_at is not None
    assert user.updated_at is None

    identity = Identity(user=user, provider=Provider.google, provider_sub="sub")
    async_session.add(identity)
    await async_session.flush()
    await async_session.refresh(user)
    assert len(user.identities) == 1
    