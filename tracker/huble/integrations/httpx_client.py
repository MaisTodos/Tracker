# huble/integrations/httpx_client.py
from __future__ import annotations
from ..interfaces import IHttpClientAdapter
from ..core import CANON_TRACE_HEADER, get_current_trace_id

class HttpxClientAdapter(IHttpClientAdapter):
    _patched = False
    def patch(self) -> None:
        if self._patched:
            return
        try:
            import httpx
        except Exception:
            return

        self._patched = True
        _orig_client_request = httpx.Client.request
        _orig_async_client_request = httpx.AsyncClient.request
        _orig_client_send = httpx.Client.send
        _orig_async_client_send = httpx.AsyncClient.send

        def _inject_dict(headers):
            tid = get_current_trace_id()
            if not tid:
                return headers
            base = dict(headers or {})
            if CANON_TRACE_HEADER not in {k.lower(): v for k,v in base.items()}:
                base[CANON_TRACE_HEADER] = tid
            return base

        def _client_request(self, method, url, *args, headers=None, **kw):
            return _orig_client_request(self, method, url, *args, headers=_inject_dict(headers), **kw)

        async def _async_client_request(self, method, url, *args, headers=None, **kw):
            return await _orig_async_client_request(self, method, url, *args, headers=_inject_dict(headers), **kw)

        def _client_send(self, request, *args, **kw):
            tid = get_current_trace_id()
            if tid and CANON_TRACE_HEADER not in request.headers:
                request.headers[CANON_TRACE_HEADER] = tid
            return _orig_client_send(self, request, *args, **kw)

        async def _async_client_send(self, request, *args, **kw):
            tid = get_current_trace_id()
            if tid and CANON_TRACE_HEADER not in request.headers:
                request.headers[CANON_TRACE_HEADER] = tid
            return await _orig_async_client_send(self, request, *args, **kw)

        httpx.Client.request = _client_request
        httpx.AsyncClient.request = _async_client_request
        httpx.Client.send = _client_send
        httpx.AsyncClient.send = _async_client_send
