import types
import logging
import sys
import pytest

class MemoryHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []
    def emit(self, record):
        self.records.append(record)

@pytest.fixture
def mem_logger():
    root = logging.getLogger()
    handler = MemoryHandler()
    root.addHandler(handler)
    try:
        yield handler
    finally:
        root.removeHandler(handler)

def stub_module(monkeypatch, fullname: str, attrs: dict | None = None):
    mod = types.ModuleType(fullname)
    for k, v in (attrs or {}).items():
        setattr(mod, k, v)
    # Garantir a hierarquia (pacotes) existe em sys.modules
    parts = fullname.split(".")
    pkg = ""
    for i, part in enumerate(parts):
        pkg = part if i == 0 else f"{pkg}.{part}"
        if pkg not in sys.modules:
            sys.modules[pkg] = types.ModuleType(pkg)
    monkeypatch.setitem(sys.modules, fullname, mod)
    return mod
