import re
from app.utils import refresh_tools as rt
from app.core.config import settings


def test_generate_and_hash_refresh():
    plain1 = rt.generate_refresh_plain()
    plain2 = rt.generate_refresh_plain()
    assert plain1 != plain2
    assert len(plain1) >= 86
    h = rt.hash_refresh(plain1)
    assert re.fullmatch(r"[0-9a-f]{64}", h)


def test_redis_key_generation(monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "production")
    token_hash = "abc123"
    user_id = "user1"
    tk = rt.redis_token_key(token_hash)
    uk = rt.redis_user_set_key(user_id)
    assert tk == f"prod:{settings.REFRESH_REDIS_PREFIX}{token_hash}"
    assert uk == f"prod:{settings.REFRESH_USER_SET_PREFIX}{user_id}"


def test_exp_ts():
    now = rt.now_ts()
    exp = rt.exp_ts()
    diff = exp - now
    assert settings.REFRESH_EXPIRES_SEC - 1 <= diff <= settings.REFRESH_EXPIRES_SEC + 1


def test_json_roundtrip():
    rec = rt.RefreshRecord(user_id="u1", iat=rt.now_ts(), exp=rt.exp_ts())
    s = rt.to_json(rec)
    assert rt.from_json(s) == rec
