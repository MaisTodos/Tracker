import time
from typing import Callable, Dict, Any, Optional
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from ...huble.core import (
    CANON_TRACE_HEADER, get_trace_id_if_any,
    set_current_trace_id, reset_current_trace_id, ensure_current_trace_id
)

class HubleTraceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        incoming = get_trace_id_if_any(request.headers)
        trace_id = incoming or str(uuid4())
        token = set_current_trace_id(trace_id)
        try:
            response: Response = await call_next(request)
        finally:
            reset_current_trace_id(token)
        response.headers[CANON_TRACE_HEADER] = trace_id
        return response

class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, logger, redact_headers: Optional[set[str]] = None):
        super().__init__(app)
        self.logger = logger
        self.redact_headers = {h.lower() for h in (redact_headers or set())}

    async def dispatch(self, request: Request, call_next: Callable):
        trace_id = ensure_current_trace_id()

        t0 = time.perf_counter()
        try:
            response: Response = await call_next(request)
            status = response.status_code
        except Exception as exc:
            status = 500
            self.logger.exception("unhandled_exception", extra={
                "trace_id": trace_id,
                "path": request.url.path,
                "method": request.method,
                "reason": str(exc),
            })
            raise
        finally:
            dt = time.perf_counter() - t0

        def _clean(h) -> Dict[str, str]:
            out: Dict[str, str] = {}
            for k, v in h.items():
                kl = k.lower()
                out[kl] = "***REDACTED***" if kl in self.redact_headers else str(v)
            return out

        self.logger.info("http_request",
            extra={
                "trace_id": trace_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": (request.headers.get("x-forwarded-for") or "").split(",")[0].strip() or (request.client.host if request.client else None),
                "req_headers": _clean(request.headers),
                "res_headers": _clean(response.headers),
                "status": status,
                "time_taken_ms": round(dt * 1000, 2),
            },
        )
        return response
