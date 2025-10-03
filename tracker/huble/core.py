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
