# huble/integrations/django_fw.py
from __future__ import annotations
from typing import Any, Optional, Iterable
from django.utils.deprecation import MiddlewareMixin
from ..interfaces import IFrameworkAdapter
from ..core import (
    CANON_TRACE_HEADER, get_or_create_trace_id, set_current_trace_id, reset_current_trace_id
)
import time, json

class HubleTraceMiddleware(MiddlewareMixin):
    def process_request(self, request):
        tid, _ = get_or_create_trace_id(getattr(request, "headers", {}))
        token = set_current_trace_id(tid)
        request._huble_trace_id = tid
        request._huble_trace_token = token
        request._huble_start = time.perf_counter()

    def process_response(self, request, response):
        tid = getattr(request, "_huble_trace_id", None)
        tok = getattr(request, "_huble_trace_token", None)
        if tid: response[CANON_TRACE_HEADER] = tid
        if tok: reset_current_trace_id(tok)
        return response

class RequestResponseLoggingMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None, logger=None, redact_headers=None):
        super().__init__(get_response)
        self.logger = logger
        self.redact = {*(redact_headers or {"authorization","cookie","x-api-key"})}

    def process_response(self, request, response):
        if not self.logger:
            return response
        try:
            elapsed = None
            if hasattr(request, "_huble_start"):
                elapsed = round((time.perf_counter()-request._huble_start)*1000, 2)
            hdrs = getattr(request, "headers", {})
            safe_headers = {
                str(k).lower(): ("***REDACTED***" if str(k).lower() in self.redact else str(v))
                for k, v in hdrs.items()
            }
            self.logger.info(json.dumps({
                "event":"http_cycle","framework":"django",
                "trace_id": getattr(request,"_huble_trace_id",None),
                "method": getattr(request,"method",None),
                "path": getattr(request,"path",None),
                "status_code": getattr(response,"status_code",None),
                "elapsed_ms": elapsed, "headers": safe_headers
            }))
        except Exception:
            pass
        return response

class DjangoFrameworkAdapter(IFrameworkAdapter):
    def attach(self, app: Any, **kwargs) -> Any:
        
        return app
