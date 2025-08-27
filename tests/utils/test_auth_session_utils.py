import json
import pytest
from fakeredis.aioredis import FakeRedis
from app.utils import auth_session as a_sess

@pytest.mark.asyncio
async def test_create_auth_session_and_status(monkeypatch):
    r = FakeRedis(decode_responses=True)
    data = await a_sess.create_auth_session(r, "verifier-xyz")
    assert "session_id" in data and "auth_url" in data
    sid = data["session_id"]

    status, result, err = await a_sess.get_status(r, sid)
    assert status == "pending" and result is None and err is None
    assert await a_sess.get_code_verifier(r, sid) == "verifier-xyz"

    await a_sess.set_result(r, sid, {"ok": True})
    status, result, err = await a_sess.get_status(r, sid)
    assert status == "ready" and result == {"ok": True} and err is None

    await a_sess.set_error(r, sid, "oops")
    status, result, err = await a_sess.get_status(r, sid)
    assert status == "error" and result is None and err == "oops"
