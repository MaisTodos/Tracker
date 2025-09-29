import time
from typing import Optional, Dict
from django.utils.deprecation import MiddlewareMixin
from ..core import (
    CANON_TRACE_HEADER,
    get_trace_id_if_any,
    set_current_trace_id,
    reset_current_trace_id,
    ensure_current_trace_id,
)

class HubleTraceMiddleware(MiddlewareMixin):
    """Garante entrada/saída do X-HUBLE-TRACE-ID no ciclo Django/DRF."""
    def process_request(self, request):
        incoming = get_trace_id_if_any(request.headers)
        self._token = set_current_trace_id(incoming or ensure_current_trace_id())

    def process_response(self, request, response):
        try:
            tid = ensure_current_trace_id()
            response[CANON_TRACE_HEADER] = tid
        finally:
            token = getattr(self, "_token", None)
            if token is not None:
                reset_current_trace_id(token)
        return response


class RequestResponseLoggingMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None, *, logger=None, redact_headers: Optional[set[str]] = None):
        super().__init__(get_response)
        self.logger = logger
        self.redact_headers = {h.lower() for h in (redact_headers or set())}

    def process_request(self, request):
        self._t0 = time.perf_counter()
        ensure_current_trace_id()

    def process_response(self, request, response):
        dt = (time.perf_counter() - getattr(self, "_t0", time.perf_counter())) * 1000.0
        def _clean(django_headers) -> Dict[str, str]:
            out = {}
            for k, v in django_headers.items():
                kl = str(k).lower()
                out[kl] = "***REDACTED***" if kl in self.redact_headers else str(v)
            return out

        if self.logger:
            try:
                path = request.get_full_path() if hasattr(request, "get_full_path") else request.path
                self.logger.info("http_request", extra={
                    "method": request.method,
                    "path": path,
                    "status": getattr(response, "status_code", None),
                    "req_headers": _clean(request.headers),
                    "res_headers": _clean(getattr(response, "headers", {})),
                    "time_taken_ms": round(dt, 2),
                })
            except Exception:
                pass
        return response
