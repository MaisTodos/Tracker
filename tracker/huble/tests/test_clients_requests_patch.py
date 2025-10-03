import types
from huble import enable_clients
from core import set_current_trace_id, reset_current_trace_id, CANON_TRACE_HEADER

def test_requests_patch_injeta_header(monkeypatch):
    class Session:
        def __init__(self):
            self.last_kwargs = None
        def request(self, method, url, **kwargs):
            self.last_kwargs = kwargs
            return types.SimpleNamespace(status_code=200)

    sess_mod = types.ModuleType("requests.sessions")
    sess_mod.Session = Session

    req_mod = types.ModuleType("requests")
    req_mod.sessions = sess_mod

    sys = __import__("sys")
    monkeypatch.setitem(sys.modules, "requests", req_mod)
    monkeypatch.setitem(sys.modules, "requests.sessions", sess_mod)

    enable_clients(["requests"])

    tok = set_current_trace_id("4a750618-2ad1-494f-9142-bbe0a6e55874")
    try:
        s = Session()
        s.request("GET", "http://x")
        hdrs = s.last_kwargs.get("headers", {})
        assert hdrs[CANON_TRACE_HEADER] == "4a750618-2ad1-494f-9142-bbe0a6e55874"
    finally:
        reset_current_trace_id(tok)
