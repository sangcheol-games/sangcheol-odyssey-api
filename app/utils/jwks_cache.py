from __future__ import annotations
import time
import httpx
from typing import Any

class JWKSCache:
    def __init__(self, url: str, ttl: int = 3600):
        self.url = url
        self.ttl = ttl
        self._jwks: dict[str, Any] | None = None
        self._exp: float = 0.0

    async def get(self) -> dict[str, Any]:
        now = time.time()
        if self._jwks and now < self._exp:
            return self._jwks
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(self.url)
            r.raise_for_status()
            self._jwks = r.json()
            self._exp = now + self.ttl
            return self._jwks
