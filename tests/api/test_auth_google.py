import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock
from app.main import app
from app.core.session import get_session
from app.api.v1.endpoints import auth_google

@pytest.mark.asyncio
async def test_google_exchange(monkeypatch, client):
    async def override_session():
        yield AsyncMock()
    app.dependency_overrides[get_session] = override_session

    monkeypatch.setattr(auth_google.settings, "GOOGLE_CLIENT_ID_WEB", "cid")
    monkeypatch.setattr(auth_google.settings, "GOOGLE_REDIRECT_URI", "redir")

    async def fake_exchange(req):
        return SimpleNamespace(id_token="id")

    async def fake_verify(token):
        return {"sub": "s"}

    async def fake_handle(db, claims):
        return {"access_token": "a", "expires_in": 3600, "is_new_user": False, "token_type": "bearer"}

    monkeypatch.setattr(auth_google, "exchange_google_token", fake_exchange)
    monkeypatch.setattr(auth_google, "verify_google_id_token", fake_verify)
    monkeypatch.setattr(auth_google, "handle_google_login", fake_handle)

    resp = await client.post("/v1/auth/google/exchange", json={"code": "c", "code_verifier": "v"})
    assert resp.status_code == 200
    assert resp.json()["access_token"] == "a"
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_google_verify_id_token(monkeypatch, client):
    async def override_session():
        yield AsyncMock()
    app.dependency_overrides[get_session] = override_session

    async def fake_verify(token):
        return {"sub": "s"}

    async def fake_handle(db, claims):
        return {"access_token": "a", "expires_in": 3600, "is_new_user": False, "token_type": "bearer"}

    monkeypatch.setattr(auth_google, "verify_google_id_token", fake_verify)
    monkeypatch.setattr(auth_google, "handle_google_login", fake_handle)

    resp = await client.post("/v1/auth/google/verify-id-token", json={"id_token": "t"})
    assert resp.status_code == 200
    assert resp.json()["access_token"] == "a"
    app.dependency_overrides.clear()
