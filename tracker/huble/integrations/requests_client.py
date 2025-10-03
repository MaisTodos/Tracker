from __future__ import annotations
from ..interfaces import IHttpClientAdapter
from ..core import CANON_TRACE_HEADER, get_current_trace_id

class RequestsClientAdapter(IHttpClientAdapter):
    _patched = False
    def patch(self) -> None:
        if self._patched:
            return
        try:
            import requests
        except Exception:
            return

        self._patched = True
        _orig = requests.sessions.Session.request

        def _session_request(self, method, url, **kw):
            tid = get_current_trace_id()
            if tid:
                hdrs = dict(kw.get("headers") or {})
                if CANON_TRACE_HEADER.lower() not in {k.lower() for k in hdrs}:
                    hdrs[CANON_TRACE_HEADER] = tid
                kw["headers"] = hdrs
            return _orig(self, method, url, **kw)

        requests.sessions.Session.request = _session_request
