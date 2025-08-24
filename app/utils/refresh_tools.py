from __future__ import annotations
import secrets, hmac, hashlib, json
from datetime import datetime, timezone
from typing import TypedDict
from app.core.config import settings

class RefreshRecord(TypedDict):
    user_id: str
    iat: int
    exp: int

def now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())

def exp_ts() -> int:
    return now_ts() + int(settings.REFRESH_EXPIRES_SEC)

def _pepper() -> bytes:
    return (settings.REFRESH_HASH_PEPPER or settings.JWT_SECRET).encode("utf-8")

def generate_refresh_plain() -> str:
    return secrets.token_urlsafe(64)

def hash_refresh(plain: str) -> str:
    return hmac.new(_pepper(), plain.encode("utf-8"), hashlib.sha256).hexdigest()

def _env_prefix() -> str:
    raw = (getattr(settings, "APP_ENV", "") or "").strip().lower()
    mapping = {
        "dev": "dev", "development": "dev",
        "stg": "stg", "stage": "stg", "staging": "stg",
        "prod": "prod", "production": "prod",
    }
    env = mapping.get(raw, "dev")
    return env + ":"

def redis_token_key(token_hash: str) -> str:
    return f"{_env_prefix()}{settings.REFRESH_REDIS_PREFIX}{token_hash}"

def redis_user_set_key(user_id: str) -> str:
    return f"{_env_prefix()}{settings.REFRESH_USER_SET_PREFIX}{user_id}"

def to_json(record: RefreshRecord) -> str:
    return json.dumps(record)

def from_json(s: str) -> RefreshRecord:
    return json.loads(s)
