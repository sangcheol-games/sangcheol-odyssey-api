import pytest
from fakeredis.aioredis import FakeRedis
from app.utils import auth_session as a_sess

VALID_VERIFIER = "A" * 50  # 50 chars, RFC 7636 valid

@pytest.mark.asyncio
async def test_create_auth_session_and_status():
    r = FakeRedis(decode_responses=True)
    data = await a_sess.create_auth_session(r, VALID_VERIFIER)
    assert "session_id" in data and "auth_url" in data
    sid = data["session_id"]

    status, result, err = await a_sess.get_status(r, sid)
    assert status == "pending" and result is None and err is None
    assert await a_sess.get_code_verifier(r, sid) == VALID_VERIFIER

    await a_sess.set_result(r, sid, {"ok": True})
    status, result, err = await a_sess.get_status(r, sid)
    assert status == "ready"
    assert result == {"ok": True}
    assert err is None

    await a_sess.set_error(r, sid, "oops")
    status, result, err = await a_sess.get_status(r, sid)
    assert status == "error"
    assert result is None
    assert err == "oops"
