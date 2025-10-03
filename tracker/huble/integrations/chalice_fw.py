from __future__ import annotations
from typing import Any, Optional, Iterable, Callable
from ..interfaces import IFrameworkAdapter
from ..core import (
    CANON_TRACE_HEADER, get_or_create_trace_id, set_current_trace_id, reset_current_trace_id
)
import time, json

def _with_trace(log_request_response: bool=False, logger=None, redact_headers=None):
    redact = {*(redact_headers or {"authorization","cookie","x-api-key"})}
    def deco(fn: Callable):
        def wrapper(*args, **kwargs):
            from chalice import current_app, Response
            req = current_app.current_request
            tid, _ = get_or_create_trace_id(req.headers or {})
            tok = set_current_trace_id(tid)
            try:
                start = time.perf_counter() if log_request_response else None
                rv = fn(*args, **kwargs)
                if log_request_response and logger:
                    try:
                        elapsed = round((time.perf_counter()-start)*1000, 2) if start else None
                        safe_headers = {
                            str(k).lower(): ("***REDACTED***" if str(k).lower() in redact else str(v))
                            for k, v in (req.headers or {}).items()
                        }
                        logger.info(json.dumps({
                            "event":"http_cycle","framework":"chalice",
                            "trace_id": tid, "method": req.method,
                            "path": req.context.get("path") or req.context.get("resourcePath"),
                            "status_code": 200, "elapsed_ms": elapsed, "headers": safe_headers
                        }))
                    except Exception:
                        pass
                if isinstance(rv, Response):
                    rv.headers[CANON_TRACE_HEADER] = tid
                    return rv
                # tuple/dict simples
                return rv, 200, {CANON_TRACE_HEADER: tid}
            finally:
                reset_current_trace_id(tok)
        return wrapper
    return deco

def _autowrap(app, **opts):
    for route in list(app.routes.values()):
        for method, view in list(route.view_functions.items()):
            route.view_functions[method] = _with_trace(**opts)(view)

class ChaliceFrameworkAdapter(IFrameworkAdapter):
    def attach(
        self, app: Any, *, log_request_response: bool=False, logger=None, redact_headers=None
    ) -> Any:
        _autowrap(app, log_request_response=log_request_response, logger=logger, redact_headers=redact_headers)
        return app
