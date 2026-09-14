import contextlib
import pytest
from unittest.mock import patch
import httpx
from httpx import Response
from app.core.config import settings

MOCK_SUCCESS_PARAMS = {
    "result": "OK",
    "steamid": "76561198000000001",
    "ownersteamid": "76561198000000001",
    "vacbanned": False,
    "publisherbanned": False,
}

@contextlib.contextmanager
def mock_steam_api(response_or_exc):
    real_get = httpx.AsyncClient.get

    async def selective_get(self, url, *args, **kwargs):
        if "steampowered.com" in str(url):
            if isinstance(response_or_exc, Exception):
                raise response_or_exc
            return response_or_exc
        return await real_get(self, url, *args, **kwargs)

    with patch("httpx.AsyncClient.get", new=selective_get):
        yield

@pytest.mark.asyncio
async def test_steam_login_success(client, async_session):
    mock_response = Response(200, json={"response": {"params": MOCK_SUCCESS_PARAMS}})

    with mock_steam_api(mock_response):
        response = await client.post(
            "/v1/auth/steam/login",
            json={"ticket": "mock_valid_ticket_hex_string"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["is_new_user"] is True

@pytest.mark.asyncio
async def test_steam_login_existing_user(client, async_session):
    mock_response = Response(200, json={"response": {"params": MOCK_SUCCESS_PARAMS}})

    with mock_steam_api(mock_response):
        # 1st login: new user
        res1 = await client.post(
            "/v1/auth/steam/login",
            json={"ticket": "ticket_1"}
        )
        assert res1.status_code == 200
        assert res1.json()["is_new_user"] is True

        # 2nd login with same steamid: existing user
        res2 = await client.post(
            "/v1/auth/steam/login",
            json={"ticket": "ticket_2"}
        )
        assert res2.status_code == 200
        assert res2.json()["is_new_user"] is False

@pytest.mark.asyncio
async def test_steam_login_and_access_protected_endpoint(client, async_session):
    mock_response = Response(200, json={"response": {"params": MOCK_SUCCESS_PARAMS}})

    with mock_steam_api(mock_response):
        login_res = await client.post(
            "/v1/auth/steam/login",
            json={"ticket": "mock_valid_ticket"}
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]

        # Call protected /v1/users/me endpoint
        me_res = await client.get(
            "/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_res.status_code == 200
        user_data = me_res.json()
        assert "id" in user_data
        assert user_data["uid"] is not None

@pytest.mark.asyncio
async def test_steam_login_invalid_ticket(client):
    mock_response = Response(200, json={
        "response": {
            "error": {
                "errordesc": "Invalid ticket"
            }
        }
    })

    with mock_steam_api(mock_response):
        response = await client.post(
            "/v1/auth/steam/login",
            json={"ticket": "invalid_ticket"}
        )

        assert response.status_code == 400
        assert "Invalid steam ticket" in response.json()["detail"]

@pytest.mark.asyncio
async def test_steam_login_result_not_ok(client):
    mock_response = Response(200, json={
        "response": {
            "params": {
                "result": "Fail"
            }
        }
    })

    with mock_steam_api(mock_response):
        response = await client.post(
            "/v1/auth/steam/login",
            json={"ticket": "failed_ticket"}
        )

        assert response.status_code == 400
        assert "Invalid steam ticket: Fail" in response.json()["detail"]

@pytest.mark.asyncio
async def test_steam_login_upstream_server_error(client):
    mock_response = Response(500, text="Internal Server Error")

    with mock_steam_api(mock_response):
        response = await client.post(
            "/v1/auth/steam/login",
            json={"ticket": "any_ticket"}
        )

        assert response.status_code == 502
        assert "Steam authentication request failed: 500" in response.json()["detail"]

@pytest.mark.asyncio
async def test_steam_login_network_error(client):
    with mock_steam_api(httpx.ConnectError("Connection refused")):
        response = await client.post(
            "/v1/auth/steam/login",
            json={"ticket": "any_ticket"}
        )

        assert response.status_code == 502
        assert "Failed to communicate with Steam authentication servers" in response.json()["detail"]

@pytest.mark.asyncio
async def test_steam_login_missing_api_key(client, monkeypatch):
    monkeypatch.setattr(settings, "STEAM_WEB_API_KEY", None)

    response = await client.post(
        "/v1/auth/steam/login",
        json={"ticket": "any_ticket"}
    )

    assert response.status_code == 500
    assert "STEAM_WEB_API_KEY is missing" in response.json()["detail"]

