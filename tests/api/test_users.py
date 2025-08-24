import uuid
import pytest
from types import SimpleNamespace
from datetime import datetime, timezone
from app.main import app
from app.core.session import get_session
from app.deps.auth import get_current_user, get_current_user_id
from app.api.v1.endpoints import users

@pytest.mark.asyncio
async def test_users_me(client):
    user = SimpleNamespace(
        id=uuid.uuid4(),
        uid="u",
        nickname="n",
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        last_login_at=None,
    )
    app.dependency_overrides[get_current_user] = lambda: user
    resp = await client.get("/v1/users/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["uid"] == "u"
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_set_nickname(monkeypatch, client):
    db = SimpleNamespace()
    async def override_session():
        yield db
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_current_user_id] = lambda: "user"

    class DummySvc:
        def __init__(self, db):
            pass
        async def update_nickname_once(self, user_id, nickname):
            return SimpleNamespace(
                id=uuid.uuid4(),
                uid="u",
                nickname=nickname,
                created_at=datetime.now(timezone.utc),
                updated_at=None,
                last_login_at=None,
            )

    monkeypatch.setattr(users, "UserService", DummySvc)

    resp = await client.patch("/v1/users/me/nickname", json={"nickname": "new"})
    assert resp.status_code == 200
    assert resp.json()["nickname"] == "new"
    app.dependency_overrides.clear()
