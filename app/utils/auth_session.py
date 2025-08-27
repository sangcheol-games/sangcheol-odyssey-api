from __future__ import annotations
import json, time, secrets, hashlib, base64
from typing import Any
from redis.asyncio import Redis

SESSION_PREFIX = "authsess:"
SESSION_TTL = 600

def _key(sid: str) -> str:
    return f"{SESSION_PREFIX}{sid}"

def _now() -> int:
    return int(time.time())

def _sid() -> str:
    raw = secrets.token_urlsafe(32)
    h = hashlib.sha256(raw.encode()).digest()
    return base64.urlsafe_b64encode(h)[:32].decode()

def _nonce() -> str:
    return secrets.token_urlsafe(16)

async def create_auth_session(r: Redis, code_verifier: str) -> dict[str, str]:
    sid = _sid()
    nonce = _nonce()
    rec = {
        "status": "pending",
        "code_verifier": code_verifier,
        "nonce": nonce,
        "created_at": _now(),
        "result": None,
        "error": None,
    }
    await r.setex(_key(sid), SESSION_TTL, json.dumps(rec))
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&scope=openid%20email%20profile&code_challenge_method=S256&state={sid}&nonce={nonce}"
    return {"session_id": sid, "auth_url": auth_url}

async def get_status(r: Redis, sid: str) -> tuple[str, Any | None, str | None]:
    raw = await r.get(_key(sid))
    if not raw:
        return "not_found", None, None
    rec = json.loads(raw)
    st = rec.get("status")
    if st == "ready":
        return "ready", rec.get("result"), None
    if st == "error":
        return "error", None, rec.get("error")
    return "pending", None, None

async def get_code_verifier(r: Redis, sid: str) -> str | None:
    raw = await r.get(_key(sid))
    if not raw:
        return None
    return json.loads(raw).get("code_verifier")

async def set_result(r: Redis, sid: str, result: Any) -> None:
    raw = await r.get(_key(sid))
    if not raw:
        return
    rec = json.loads(raw)
    rec["status"] = "ready"
    rec["result"] = result
    await r.setex(_key(sid), SESSION_TTL, json.dumps(rec))

async def set_error(r: Redis, sid: str, message: str) -> None:
    raw = await r.get(_key(sid))
    if not raw:
        return
    rec = json.loads(raw)
    rec["status"] = "error"
    rec["error"] = message
    await r.setex(_key(sid), SESSION_TTL, json.dumps(rec))
