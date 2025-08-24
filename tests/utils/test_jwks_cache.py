import pytest
import httpx
from types import SimpleNamespace

from app.utils.jwks_cache import JWKSCache


@pytest.mark.asyncio
async def test_jwks_cache(monkeypatch):
    calls = SimpleNamespace(count=0)

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            calls.count += 1

            class Resp:
                def json(self):
                    return {"keys": ["k"]}

                def raise_for_status(self):
                    pass

            return Resp()

    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: DummyClient())

    cache = JWKSCache("http://example")
    jwks1 = await cache.get()
    jwks2 = await cache.get()
    assert jwks1 == jwks2
    assert calls.count == 1
