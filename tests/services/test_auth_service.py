import uuid
from types import SimpleNamespace

import pytest
from pytest import raises
from unittest.mock import AsyncMock

import httpx

from fastapi import HTTPException

from app.schemas.google_oauth import GoogleTokenRequest, GoogleIdClaims
from app.services import auth_service


@pytest.mark.asyncio
async def test_exchange_google_token_success(monkeypatch):
    req = GoogleTokenRequest(
        client_id="cid",
        client_secret="sec",
        code="code",
        redirect_uri="uri",
        code_verifier="ver",
    )

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, data):
            class Resp:
                status_code = 200

                def json(self):
                    return {"id_token": "id"}

            return Resp()

    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: DummyClient())
    resp = await auth_service.exchange_google_token(req)
    assert resp.id_token == "id"


@pytest.mark.asyncio
async def test_exchange_google_token_failure(monkeypatch):
    req = GoogleTokenRequest(
        client_id="cid",
        client_secret="sec",
        code="code",
        redirect_uri="uri",
        code_verifier="ver",
    )

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, data):
            class Resp:
                status_code = 400

                def json(self):
                    return {}

            return Resp()

    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: DummyClient())
    with raises(HTTPException):
        await auth_service.exchange_google_token(req)


@pytest.mark.asyncio
async def test_verify_google_id_token(monkeypatch):
    monkeypatch.setattr(auth_service.settings, "GOOGLE_CLIENT_IDS", "client")

    async def fake_get():
        return {"keys": []}

    class MockClaims(dict):
        def validate(self, leeway):
            return True

    class MockRs256:
        def decode(self, token, keyset, claims_options):
            return MockClaims(
                {
                    "aud": "client",
                    "iss": "https://accounts.google.com",
                    "sub": "sub123",
                    "email": "e@example.com",
                    "email_verified": True,
                }
            )

    monkeypatch.setattr(auth_service._jwks_cache, "get", fake_get)
    monkeypatch.setattr(auth_service, "_rs256", MockRs256())

    claims = await auth_service.verify_google_id_token("token")
    assert claims.sub == "sub123"
    assert claims.email == "e@example.com"


@pytest.mark.asyncio
async def test_verify_google_id_token_invalid_aud(monkeypatch):
    monkeypatch.setattr(auth_service.settings, "GOOGLE_CLIENT_IDS", "client")

    async def fake_get():
        return {}

    class MockClaims(dict):
        def validate(self, leeway):
            return True

    class MockRs256:
        def decode(self, token, keyset, claims_options):
            return MockClaims(
                {
                    "aud": "other",
                    "iss": "https://accounts.google.com",
                    "sub": "sub123",
                }
            )

    monkeypatch.setattr(auth_service._jwks_cache, "get", fake_get)
    monkeypatch.setattr(auth_service, "_rs256", MockRs256())

    with raises(HTTPException):
        await auth_service.verify_google_id_token("token")


@pytest.mark.asyncio
async def test_handle_google_login_existing_user(monkeypatch):
    user_id = uuid.uuid4()
    identity = SimpleNamespace(user_id=user_id)
    user = SimpleNamespace(id=user_id)

    id_repo = SimpleNamespace(
        get_by_provider_sub=AsyncMock(return_value=identity), add=AsyncMock()
    )
    user_repo = SimpleNamespace(get=AsyncMock(return_value=user), add=AsyncMock())

    monkeypatch.setattr(auth_service, "IdentityRepository", lambda db: id_repo)
    monkeypatch.setattr(auth_service, "UserRepository", lambda db: user_repo)
    monkeypatch.setattr(auth_service, "issue_access_token", lambda uid: f"token-{uid}")

    db = SimpleNamespace(commit=AsyncMock())
    claims = GoogleIdClaims(sub="sub123", email="e@example.com", email_verified=True)

    resp = await auth_service.handle_google_login(db, claims)
    assert resp.is_new_user is False
    assert resp.access_token == f"token-{user_id}"
    id_repo.add.assert_not_awaited()
    user_repo.add.assert_not_awaited()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_google_login_new_user(monkeypatch):
    async def add_user(user):
        user.id = uuid.uuid4()
        return user

    id_repo = SimpleNamespace(
        get_by_provider_sub=AsyncMock(return_value=None), add=AsyncMock()
    )
    user_repo = SimpleNamespace(get=AsyncMock(), add=AsyncMock(side_effect=add_user))

    monkeypatch.setattr(auth_service, "IdentityRepository", lambda db: id_repo)
    monkeypatch.setattr(auth_service, "UserRepository", lambda db: user_repo)
    monkeypatch.setattr(auth_service, "issue_access_token", lambda uid: f"token-{uid}")

    db = SimpleNamespace(commit=AsyncMock())
    claims = GoogleIdClaims(sub="sub123", email="e@example.com", email_verified=True)

    resp = await auth_service.handle_google_login(db, claims)
    assert resp.is_new_user is True
    assert resp.access_token.startswith("token-")
    id_repo.add.assert_awaited_once()
    user_repo.add.assert_awaited_once()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_google_login_missing_sub(monkeypatch):
    db = SimpleNamespace(commit=AsyncMock())
    claims = GoogleIdClaims(sub=None)
    with raises(HTTPException):
        await auth_service.handle_google_login(db, claims)
