import uuid
import pytest
import app.db.base_class  # noqa: F401
from app.models.user import User
from app.repositories.user_repo import UserRepository

@pytest.mark.asyncio
async def test_user_repository_crud(async_session):
    repo = UserRepository(async_session)
    uid1 = f"user-{uuid.uuid4()}"
    uid2 = f"user-{uuid.uuid4()}"
    user = User(uid=uid1, nickname="nick")
    await repo.add(user)
    await async_session.commit()

    fetched = await repo.get(user.id)
    assert fetched.uid == uid1

    fetched_uid = await repo.get_by_uid(uid1)
    assert fetched_uid.id == user.id

    user2 = User(uid=uid2, nickname="nick")
    await repo.add(user2)
    await async_session.commit()

    users = await repo.get_all_by_nickname("nick")
    assert {u.uid for u in users} == {uid1, uid2}
