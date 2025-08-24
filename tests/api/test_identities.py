import uuid
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock
from app.main import app
from app.core.session import get_session
from app.deps.auth import get_current_user_id
from app.api.v1.endpoints import identities

@pytest.mark.asyncio
async def test_link_identity(monkeypatch, client):
    db = SimpleNamespace()
    async def override_session():
        yield db
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_current_user_id] = lambda: "user"

    class DummySvc:
        def __init__(self, db):
            self.db = db
        async def link_identity(self, user_id, provider, provider_sub, claims):
            return SimpleNamespace(id=uuid.uuid4(), provider=provider.value, provider_sub=provider_sub)

    monkeypatch.setattr(identities, "UserService", DummySvc)

    resp = await client.post("/v1/identities/google", json={"provider_sub": "sub"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "google"
    assert data["provider_sub"] == "sub"
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_unlink_identity(monkeypatch, client):
    commit = AsyncMock()
    db = SimpleNamespace(commit=commit)
    async def override_session():
        yield db
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_current_user_id] = lambda: "user"

    class DummySvc:
        def __init__(self, db):
            self.ids = SimpleNamespace(delete_returning=AsyncMock(return_value=(1, [{"provider_sub": "sub"}])))

    monkeypatch.setattr(identities, "UserService", DummySvc)

    resp = await client.delete("/v1/identities/google")
    assert resp.status_code == 200
    data = resp.json()
    assert data["deleted"] is True
    assert data["provider"] == "google"
    assert data["provider_sub"] == "sub"
    commit.assert_awaited()
    app.dependency_overrides.clear()
