import uuid
from contextvars import ContextVar
from typing import Optional, Mapping, Any

CANON_TRACE_HEADER = "X-HUBLE-TRACE-ID"

_current_trace_id: ContextVar[Optional[str]] = ContextVar("x_huble_trace_id", default=None)

def get_current_trace_id() -> Optional[str]:
    return _current_trace_id.get()

def set_current_trace_id(trace_id: str):
    return _current_trace_id.set(trace_id)

def reset_current_trace_id(token) -> None:
    try:
        _current_trace_id.reset(token)
    except Exception:
        pass

def _ci_get(headers: Mapping[str, Any], name: str) -> Optional[str]:
    nl = name.lower()
    for k, v in headers.items():
        if str(k).lower() == nl:
            return v
    return None

def _normalize_uuid(raw: str) -> Optional[str]:
    if not raw:
        return None
    s = raw.strip()
    try:
        return str(uuid.UUID(s))
    except Exception:
        try:
            return str(uuid.UUID(hex=s))
        except Exception:
            return None

def get_trace_id_if_any(headers: Mapping[str, Any]) -> Optional[str]:
    raw = _ci_get(headers, CANON_TRACE_HEADER)
    return _normalize_uuid(raw) if raw else None

def get_or_create_trace_id(headers: Mapping[str, Any]) -> tuple[str, str]:
    raw = _ci_get(headers, CANON_TRACE_HEADER)
    if raw:
        norm = _normalize_uuid(raw)
        if norm:
            return norm, CANON_TRACE_HEADER.lower()
    return str(uuid.uuid4()), "generated"

_PATCHED = False
def install_outbound_patches(header_name: str = CANON_TRACE_HEADER) -> None:
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True

    def _ci_has(h: Mapping[str, Any], name: str) -> bool:
        nl = name.lower()
        return any(str(k).lower() == nl for k in h.keys())

    try:
        import httpx
        _orig_client_request = httpx.Client.request
        _orig_async_client_request = httpx.AsyncClient.request
        _orig_client_send = httpx.Client.send
        _orig_async_client_send = httpx.AsyncClient.send

        def _inject_headers_dict(headers):
            tid = get_current_trace_id()
            if not tid:
                return headers
            base = dict(headers or {})
            if not _ci_has(base, header_name):
                base[header_name] = tid
            return base

        def _client_request(self, method, url, *args, headers=None, **kwargs):
            headers = _inject_headers_dict(headers)
            return _orig_client_request(self, method, url, *args, headers=headers, **kwargs)

        async def _async_client_request(self, method, url, *args, headers=None, **kwargs):
            headers = _inject_headers_dict(headers)
            return await _orig_async_client_request(self, method, url, *args, headers=headers, **kwargs)

        def _client_send(self, request, *args, **kwargs):
            tid = get_current_trace_id()
            if tid and header_name not in request.headers:
                request.headers[header_name] = tid
            return _orig_client_send(self, request, *args, **kwargs)

        async def _async_client_send(self, request, *args, **kwargs):
            tid = get_current_trace_id()
            if tid and header_name not in request.headers:
                request.headers[header_name] = tid
            return await _orig_async_client_send(self, request, *args, **kwargs)

        httpx.Client.request = _client_request
        httpx.AsyncClient.request = _async_client_request
        httpx.Client.send = _client_send
        httpx.AsyncClient.send = _async_client_send
    except Exception:
        pass

    try:
        import requests
        _orig_session_request = requests.sessions.Session.request
        def _session_request(self, method, url, **kwargs):
            tid = get_current_trace_id()
            if tid:
                hdrs = dict(kwargs.get("headers") or {})
                if not _ci_has(hdrs, header_name):
                    hdrs[header_name] = tid
                kwargs["headers"] = hdrs
            return _orig_session_request(self, method, url, **kwargs)
        requests.sessions.Session.request = _session_request
    except Exception:
        pass


def ensure_current_trace_id() -> str:
    """Garante que exista um trace_id na ContextVar e retorna-o."""
    tid = get_current_trace_id()
    if tid:
        return tid
    new = str(uuid.uuid4())
    set_current_trace_id(new)
    return new

def setup() -> None:
    """Atalhos para ligar cabeçalho outbound e filtro de logging."""
    from .logging.filter import HubleTraceFilter
    install_outbound_patches()
    logging.getLogger().addFilter(HubleTraceFilter())