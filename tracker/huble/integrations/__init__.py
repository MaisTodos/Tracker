from __future__ import annotations
from typing import Any, Iterable, Optional

def attach_framework(app: Any, **kwargs):
    mod = app.__class__.__module__
    if "fastapi.applications" in mod or "starlette.applications" in mod:
        from .fastapi_fw import FastAPIFrameworkAdapter
        return FastAPIFrameworkAdapter().attach(app, **kwargs)
    if "chalice.app" in mod:
        from .chalice_fw import ChaliceFrameworkAdapter
        return ChaliceFrameworkAdapter().attach(app, **kwargs)
    if "django.core.handlers" in mod or "django.core.asgi" in mod:
        from .django_fw import DjangoFrameworkAdapter
        return DjangoFrameworkAdapter().attach(app, **kwargs)
    raise RuntimeError(f"Framework não suportado: {mod}")

def attach_clients(clients: Optional[Iterable[str]] = None) -> None:
    # auto por default
    wanted = set((clients or {"httpx","requests"}))
    if "httpx" in wanted:
        try:
            import httpx  # noqa
            from .httpx_client import HttpxClientAdapter
            HttpxClientAdapter().patch()
        except Exception:
            pass
    if "requests" in wanted:
        try:
            import requests  # noqa
            from .requests_client import RequestsClientAdapter
            RequestsClientAdapter().patch()
        except Exception:
            pass
