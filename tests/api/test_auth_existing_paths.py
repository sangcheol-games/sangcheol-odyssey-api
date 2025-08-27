import pytest
from types import SimpleNamespace
from app.api.v1.endpoints import auth_google as E

@pytest.mark.asyncio
async def test_verify_id_token_endpoint(monkeypatch, client):
    async def mock_verify(id_token):
        return SimpleNamespace(sub="sub-1", email="u@test", email_verified=True)
    async def mock_handle(db, claims):
        return SimpleNamespace(access_token="a", refresh_token="r", expires_in=3600, is_new_user=True, token_type="bearer")
    monkeypatch.setattr(E, "verify_google_id_token", mock_verify)
    monkeypatch.setattr(E, "handle_google_login", mock_handle)

    res = await client.post("/v1/auth/google/verify-id-token", json={"id_token":"X"})
    assert res.status_code == 200
    j = res.json()
    assert j["access_token"] == "a"
    assert j["refresh_token"] == "r"

@pytest.mark.asyncio
async def test_refresh_rotation_ok(monkeypatch, client, fake_redis):
    from app.api.v1.endpoints import auth_tokens as T
    async def fake_rotate(db, refresh_token):
        return SimpleNamespace(access_token="rotated-acc", refresh_token="rotated-ref", expires_in=3600, token_type="bearer", is_new_user=False)
    monkeypatch.setattr(T, "rotate_refresh_and_issue", fake_rotate)

    res = await client.post("/v1/auth/refresh", json={"refresh_token":"dummy"})
    assert res.status_code == 200
    assert res.json()["access_token"] == "rotated-acc"

@pytest.mark.asyncio
async def test_logout_all_refresh_ok(monkeypatch, client):
    from app.api.v1.endpoints import auth_tokens as T
    async def fake_logout(user_id: str):
        return {"message":"ok"}
    monkeypatch.setattr(T, "logout_all_refresh", fake_logout)

    import app.deps.auth as D
    def fake_decode(token: str):
        return {"sub":"user-1"}
    monkeypatch.setattr(D, "_decode", fake_decode)

    res = await client.post("/v1/auth/logout", headers={"Authorization":"Bearer faketoken"})
    assert res.status_code == 200
    assert res.json() == {"message":"ok"}
