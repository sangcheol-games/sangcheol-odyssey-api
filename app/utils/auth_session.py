from __future__ import annotations
import json, time, secrets, hashlib, base64, re
from typing import Any
from urllib.parse import urlencode
from redis.asyncio import Redis
from app.core.config import settings

SESSION_PREFIX = "authsess:"
SESSION_TTL = 600

# PKCE verifier validation: RFC 7636 (43~128 chars, unreserved)
_VERIFIER_RE = re.compile(r"^[A-Za-z0-9\-._~]{43,128}$")

def _key(sid: str) -> str:
    return f"{SESSION_PREFIX}{sid}"

def _now() -> int:
    return int(time.time())

def _sid() -> str:
    raw = secrets.token_urlsafe(32)
    h = hashlib.sha256(raw.encode("ascii")).digest()
    return base64.urlsafe_b64encode(h).decode("ascii").rstrip("=")[:32]

def _nonce() -> str:
    return secrets.token_urlsafe(16)

def _code_challenge_from_verifier(verifier: str) -> str:
    if not _VERIFIER_RE.match(verifier):
        raise ValueError("invalid PKCE code_verifier")
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

def _build_google_auth_url(*, state: str, nonce: str, code_challenge: str) -> str:
    client_id = settings.GOOGLE_CLIENT_ID_WEB or (
        settings.google_client_id_list[0] if settings.google_client_id_list else None
    )
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    if not client_id or not redirect_uri:
        raise RuntimeError("SERVER_MISCONFIG: GOOGLE_CLIENT_ID_WEB/GOOGLE_REDIRECT_URI")

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

async def create_auth_session(r: Redis, code_verifier: str) -> dict[str, str]:
    sid = _sid()
    nonce = _nonce()
    cc = _code_challenge_from_verifier(code_verifier)

    rec = {
        "status": "pending",
        "code_verifier": code_verifier,
        "nonce": nonce,
        "created_at": _now(),
        "result": None,
        "error": None,
    }
    await r.setex(_key(sid), SESSION_TTL, json.dumps(rec))

    auth_url = _build_google_auth_url(state=sid, nonce=nonce, code_challenge=cc)
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

async def get_nonce(r: Redis, sid: str) -> str | None:
    raw = await r.get(_key(sid))
    if not raw:
        return None
    return json.loads(raw).get("nonce")

async def set_result(r: Redis, sid: str, result: Any) -> None:
    raw = await r.get(_key(sid))
    if not raw:
        return
    rec = json.loads(raw)
    rec["status"] = "ready"
    rec["result"] = result
    await r.setex(_key(sid), 30, json.dumps(rec))

async def set_error(r: Redis, sid: str, message: str) -> None:
    raw = await r.get(_key(sid))
    if not raw:
        return
    rec = json.loads(raw)
    rec["status"] = "error"
    rec["error"] = message
    await r.setex(_key(sid), 120, json.dumps(rec))
