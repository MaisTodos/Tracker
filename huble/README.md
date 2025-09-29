# Exemplos de ligação — FastAPI, Django/DRF e Chalice


---

# FastAPI

```python
# main.py
from fastapi import FastAPI
from huble import setup
from huble.httpcycle.fastapi import (
    HubleTraceMiddleware,
    RequestResponseLoggingMiddleware,  # opcional
)

setup()  # ativa patches httpx/requests + filtro de logging com trace_id

app = FastAPI()

# entrada/saída do X-HUBLE-TRACE-ID
app.add_middleware(HubleTraceMiddleware)

# (opcional) log de request/response
# app.add_middleware(
#     RequestResponseLoggingMiddleware,
#     logger=None,  # ou passe um logger configurado
#     redact_headers={"authorization","cookie","x-api-key"},
# )

@app.get("/health")
def health():
    return {"ok": True}
```

---

# Django / DRF

**asgi.py** (ou **wsgi.py**) — bootstrap cedo:
```python
# asgi.py
from huble import setup
setup()

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "seu_projeto.settings")
application = get_asgi_application()
```

**settings.py** — ligar middlewares:
```python
MIDDLEWARE = [
    "huble.httpcycle.django.HubleTraceMiddleware",              # garante X-HUBLE-TRACE-ID em entrada/saída
    # "huble.httpcycle.django.RequestResponseLoggingMiddleware",  # opcional: log de request/response
    # ... seus outros middlewares
]

# Em dev/compose, evite DisallowedHost
# ALLOWED_HOSTS = ["*", "localhost", "djangoapi"]
```

---

# Chalice

## Opção A) Auto-wrap global (todas as rotas)
```python
# app.py
from chalice import Chalice
from huble import setup
from huble.httpcycle.chalice import enable_autowrap

setup()

app = Chalice(app_name="api")
enable_autowrap(
    app,
    logger=None,                # ou passe um logger
    log_request_response=True,  # opcional
    redact_headers={"authorization","cookie"},
)

@app.route("/gamma")
def gamma():
    return {"ok": True}
```

## Opção B) Decorator por rota
```python
# app.py
from chalice import Chalice
from huble import setup
from huble.httpcycle.chalice import with_huble_trace

setup()

app = Chalice(app_name="api")

@app.route("/gamma")
@with_huble_trace(log_request_response=True, redact_headers={"authorization","cookie"})
def gamma():
    return {"ok": True}
```

> Em todos os casos acima, o `setup()` garante que **requisições HTTP de saída** (`httpx`/`requests`) carreguem o `X-HUBLE-TRACE-ID` e que **todos os logs** recebam `trace_id`.  
> Os middlewares/decorator cuidam de **capturar/gerar** o header na entrada e **devolver** o mesmo na resposta.
