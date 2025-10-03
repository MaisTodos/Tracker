import logging
from .logging.filter import HubleTraceFilter

def setup_core() -> None:
    root = logging.getLogger()
    if not any(isinstance(f, HubleTraceFilter) for f in getattr(root, "filters", [])):
        root.addFilter(HubleTraceFilter())

def enable_framework(app, **kwargs): 
    from .integrations import attach_framework
    return attach_framework(app, **kwargs)

def enable_clients(clients=None) -> None:
    from .integrations import attach_clients
    attach_clients(clients)
