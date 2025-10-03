import types
import asyncio
import pytest

from huble import enable_clients
from core import set_current_trace_id, reset_current_trace_id, CANON_TRACE_HEADER

@pytest.fixture
def stub_httpx(monkeypatch):
    class _Req:
        def __init__(self):
            self.headers = {}

    class Client:
        def __init__(self): pass
        def request(self, method, url, headers=None, **kw):
            self.last_headers = dict(headers or {})
            return types.SimpleNamespace(status_code=200)
        def send(self, request, *a, **kw):
            return types.SimpleNamespace(status_code=200)

    class AsyncClient:
        def __init__(self): pass
        async def request(self, method, url, headers=None, **kw):
            self.last_headers = dict(headers or {})
            return types.SimpleNamespace(status_code=200)
        async def send(self, request, *a, **kw):
            return types.SimpleNamespace(status_code=200)

    mod = types.ModuleType("httpx")
    mod.Client = Client
    mod.AsyncClient = AsyncClient
    monkeypatch.setitem(__import__("sys").modules, "httpx", mod)
    return mod

def test_httpx_patch_injeta_header(stub_httpx):
    enable_clients(["httpx"])  # aplica o patch no módulo stub
    tok = set_current_trace_id("4a750618-2ad1-494f-9142-bbe0a6e55874")
    try:
        c = stub_httpx.Client()
        c.request("GET", "http://x", headers={"foo": "bar"})
        assert c.last_headers[CANON_TRACE_HEADER] == "4a750618-2ad1-494f-9142-bbe0a6e55874"
    finally:
        reset_current_trace_id(tok)

@pytest.mark.asyncio
async def test_httpx_async_patch_injeta_header(stub_httpx):
    enable_clients(["httpx"])
    tok = set_current_trace_id("4a750618-2ad1-494f-9142-bbe0a6e55874")
    try:
        c = stub_httpx.AsyncClient()
        resp = await c.request("GET", "http://x")
        assert getattr(c, "last_headers")[CANON_TRACE_HEADER] == "4a750618-2ad1-494f-9142-bbe0a6e55874"
    finally:
        reset_current_trace_id(tok)
