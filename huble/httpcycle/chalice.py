import time
from functools import wraps
from typing import Optional, Callable, Dict, Any
from ..core import (
    CANON_TRACE_HEADER,
    get_trace_id_if_any,
    set_current_trace_id,
    reset_current_trace_id,
    ensure_current_trace_id,
)

def with_huble_trace(view_func: Callable = None, *, logger=None, log_request_response: bool = False, redact_headers: Optional[set[str]] = None):
    """Decorator para rotas Chalice: captura/gera trace, devolve header e (opcional) loga request/response."""
    if redact_headers is None:
        redact_headers = set()

    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from chalice import current_request, Response

            incoming = get_trace_id_if_any(current_request.headers or {})
            token = set_current_trace_id(incoming or ensure_current_trace_id())

            try:
                t0 = time.perf_counter()
                result = fn(*args, **kwargs)

                if not isinstance(result, Response):
                    from chalice import Response as ChaliceResponse
                    resp = ChaliceResponse(
                        body=result,
                        status_code=200,
                        headers={CANON_TRACE_HEADER: ensure_current_trace_id()},
                    )
                else:
            
                    result.headers = dict(result.headers or {})
                    result.headers[CANON_TRACE_HEADER] = ensure_current_trace_id()
                    resp = result

                if log_request_response and logger:
                    try:
                        def _clean(headers) -> Dict[str, str]:
                            out = {}
                            for k, v in (headers or {}).items():
                                kl = str(k).lower()
                                out[kl] = "***REDACTED***" if kl in redact_headers else str(v)
                            return out
                        dt = (time.perf_counter() - t0) * 1000.0
                        logger.info("http_request", extra={
                            "method": current_request.method,
                            "path": current_request.context.get("resourcePath", current_request.path),
                            "status": resp.status_code,
                            "req_headers": _clean(current_request.headers),
                            "res_headers": _clean(resp.headers),
                            "time_taken_ms": round(dt, 2),
                        })
                    except Exception:
                        pass

                return resp
            finally:
                reset_current_trace_id(token)
        return wrapper
    return decorator(view_func) if view_func else decorator


def enable_autowrap(app, *, logger=None, log_request_response: bool = False, redact_headers: Optional[set[str]] = None):
    """
    Monkeypatch de app.route para auto-aplicar @with_huble_trace em TODAS as rotas
    definidas depois desta chamada. Chame ANTES de declarar @app.route(...).
    """
    original_route = app.route

    def route_wrapper(*r_args, **r_kwargs):
        def registrar(fn):
            wrapped = with_huble_trace(
                fn, logger=logger, log_request_response=log_request_response, redact_headers=redact_headers
            )
            return original_route(*r_args, **r_kwargs)(wrapped)
        return registrar

    app.route = route_wrapper
    return app
