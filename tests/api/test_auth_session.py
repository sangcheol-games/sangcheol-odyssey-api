import json
import pytest
from app.utils import auth_session as a_sess

VALID_VERIFIER = "A" * 50

@pytest.mark.asyncio
async def test_session_init_returns_auth_url_and_sid(client, fake_redis):
    res = await client.post("/v1/auth/session/init", json={"code_verifier": VALID_VERIFIER})
    assert res.status_code == 200
    data = res.json()
    assert "auth_url" in data and "session_id" in data
    sid = data["session_id"]
    status, result, err = await a_sess.get_status(fake_redis, sid)
    assert status == "pending"
    cv = await a_sess.get_code_verifier(fake_redis, sid)
    assert cv == VALID_VERIFIER

@pytest.mark.asyncio
async def test_session_poll_pending(client, fake_redis):
    rec = {"status":"pending","code_verifier":"v","nonce":"n","created_at":0,"result":None,"error":None}
    sid = "S123"
    await fake_redis.setex(a_sess._key(sid), 600, json.dumps(rec))
    res = await client.get("/v1/auth/session/poll", params={"sid": sid})
    assert res.status_code == 202
    assert res.json() == {"message":"pending"}

@pytest.mark.asyncio
async def test_session_poll_ready(client, fake_redis):
    sid = "READY1"
    token = {"access_token":"acc","refresh_token":"ref","expires_in":3600,"is_new_user":False}
    rec = {"status":"ready","code_verifier":"v","nonce":"n","created_at":0,"result":token,"error":None}
    await fake_redis.setex(a_sess._key(sid), 600, json.dumps(rec))
    res = await client.get("/v1/auth/session/poll", params={"sid": sid})
    assert res.status_code == 200
    body = res.json()
    assert body["access_token"] == "acc"
    assert body["refresh_token"] == "ref"
    assert body["expires_in"] == 3600

@pytest.mark.asyncio
async def test_session_poll_error(client, fake_redis):
    sid = "ERR1"
    rec = {"status":"error","code_verifier":"v","nonce":"n","created_at":0,"result":None,"error":"google_error:access_denied"}
    await fake_redis.setex(a_sess._key(sid), 600, json.dumps(rec))
    res = await client.get("/v1/auth/session/poll", params={"sid": sid})
    assert res.status_code == 400
    assert "google_error" in res.json()["detail"]

@pytest.mark.asyncio
async def test_session_poll_not_found(client):
    res = await client.get("/v1/auth/session/poll", params={"sid": "NOPE"})
    assert res.status_code == 404
