import pytest
from unittest.mock import patch
from httpx import Response

@pytest.mark.asyncio
async def test_steam_login_success(client, async_session):
    # 1. Steam API 응답 모킹 (성공 케이스)
    mock_response = {
        "response": {
            "params": {
                "result": "OK",
                "steamid": "76561198000000001",
                "ownersteamid": "76561198000000001",
                "vacbanned": False,
                "publisherbanned": False
            }
        }
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = Response(200, json=mock_response)

        # 2. 우리 서버의 스팀 로그인 엔드포인트 호출
        response = await client.post(
            "/v1/auth/steam/login",
            json={"ticket": "mock_valid_ticket_hex_string"}
        )

        # 3. 결과 검증
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["is_new_user"] is True  # 첫 로그인이므로 True

@pytest.mark.asyncio
async def test_steam_login_invalid_ticket(client):
    # 1. Steam API 응답 모킹 (실패 케이스)
    mock_response = {
        "response": {
            "error": {
                "errordesc": "Invalid ticket"
            }
        }
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = Response(200, json=mock_response)

        response = await client.post(
            "/v1/auth/steam/login",
            json={"ticket": "invalid_ticket"}
        )

        assert response.status_code == 400
        assert "Invalid steam ticket" in response.json()["detail"]
