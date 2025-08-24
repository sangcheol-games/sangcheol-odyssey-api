import pytest
from unittest.mock import AsyncMock
from app.main import app
from app.core.session import get_session
from app.deps.auth import get_current_user_id
from app.api.v1.endpoints import auth_tokens

@pytest.mark.asyncio
async def test_refresh_token(monkeypatch, client):
    async def override_session():
        yield AsyncMock()
    app.dependency_overrides[get_session] = override_session

    async def fake_rotate(db, token):
        return {"access_token": "a", "refresh_token": "r"}
    monkeypatch.setattr(auth_tokens, "rotate_refresh_and_issue", fake_rotate)

    resp = await client.post("/v1/auth/refresh", json={"refresh_token": "tok"})
    assert resp.status_code == 200
    assert resp.json() == {"access_token": "a", "refresh_token": "r"}
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_logout_all_refresh(monkeypatch, client):
    app.dependency_overrides[get_current_user_id] = lambda: "user"

    async def fake_logout(uid):
        return {"logout": True, "uid": uid}
    monkeypatch.setattr(auth_tokens, "logout_all_refresh", fake_logout)

    resp = await client.post("/v1/auth/logout")
    assert resp.status_code == 200
    assert resp.json() == {"logout": True, "uid": "user"}
    app.dependency_overrides.clear()
