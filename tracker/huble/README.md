Tracker — Integração do X-HUBLE-TRACE-ID (FastAPI, Django, Chalice)

Este README mostra como ligar a lib do trace id e dos logs nos três frameworks que você usa: FastAPI, Django (DRF) e Chalice — de forma modular, sem dependências cruzadas.
A lib garante que:

toda requisição entra com um X-HUBLE-TRACE-ID (se não vier, a lib cria um UUID v4);

o X-HUBLE-TRACE-ID é propagado no contexto e adicionado automaticamente no response;

chamadas outbound via httpx/requests recebem o header automaticamente;

todos os logs ganham o campo huble_trace_id.

APIs públicas principais:

from tracker.huble import setup_core, enable_framework, enable_clients
from tracker.huble.core import CANON_TRACE_HEADER, get_current_trace_id
# CANON_TRACE_HEADER == "X-HUBLE-TRACE-ID"


setup_core() → instala o filtro de log para incluir huble_trace_id em todos os logs.

enable_framework(app, log_request_response=False) → pluga o middleware/hook do framework detectado.

enable_clients(wanted=None) → aplica patch em httpx e requests para enviar o header automaticamente
(wanted pode ser ["httpx"], ["requests"] ou None para ambos).

1) FastAPI

main.py

import logging
from fastapi import FastAPI
from tracker.huble import setup_core, enable_framework, enable_clients
from tracker.huble.core import CANON_TRACE_HEADER, get_current_trace_id

# 1) Inicializa logging + trace-id em logs
setup_core()

# 2) Aplica patch de clients (httpx/requests) para outbound
enable_clients()  # ou enable_clients(["httpx"]) / enable_clients(["requests"])

# 3) Cria app e liga o middleware
app = FastAPI()
enable_framework(app, log_request_response=True)  # opcional: log detalhado de request/response

@app.get("/health")
def health():
    return {
        "ok": True,
        "trace_id_in_context": get_current_trace_id(),
    }


Testes rápidos

# 1) Sem header → a lib cria um UUID e retorna no response:
curl -i http://localhost:8000/health

# 2) Com header fixo → a lib respeita e propaga:
curl -i -H "X-HUBLE-TRACE-ID: 4a750618-2ad1-494f-9142-bbe0a6e55874" \
  http://localhost:8000/health

2) Django (com DRF ou não)
2.1. Habilitar o middleware

settings.py

MIDDLEWARE = [
    # Coloque o Huble cedo na cadeia
    "tracker.huble.integrations.django_fw.HubleMiddleware",
    # ... seus outros middlewares ...
]


Em dev dentro de Docker Compose, lembre de ajustar ALLOWED_HOSTS para aceitar o host/container (ex.: ALLOWED_HOSTS = ["*", "django_api", "localhost"]).

2.2. Inicializar a lib no startup do Django

Crie um AppConfig para rodar código de inicialização:

core/apps.py

from django.apps import AppConfig
from tracker.huble import setup_core, enable_clients

class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        # 1) logging + trace em logs
        setup_core()
        # 2) patch de clients p/ outbound
        enable_clients()  # httpx/requests, conforme usado no projeto


settings.py

INSTALLED_APPS = [
    "core.apps.CoreConfig",  # <-- registre o AppConfig
    # ... suas outras apps ...
]

2.3. Exemplo de view
# views.py
from django.http import JsonResponse
from tracker.huble.core import get_current_trace_id

def health(request):
    return JsonResponse({
        "ok": True,
        "trace_id_in_context": get_current_trace_id(),
    })


Testes rápidos

# Sem header → a lib cria e envia de volta
curl -i http://localhost:8000/health

# Com header fixo
curl -i -H "X-HUBLE-TRACE-ID: 4a750618-2ad1-494f-9142-bbe0a6e55874" \
  http://localhost:8000/health

3) Chalice

app.py

from chalice import Chalice
from tracker.huble import setup_core, enable_framework, enable_clients
from tracker.huble.core import get_current_trace_id

app = Chalice(app_name="my-chalice-app")

# 1) logging + trace nos logs
setup_core()

# 2) patch de clients p/ outbound
enable_clients()

# 3) integra com o Chalice (hooks para request/response)
enable_framework(app, log_request_response=True)

@app.route("/health")
def health():
    return {"ok": True, "trace_id_in_context": get_current_trace_id()}


Testes rápidos

# Chalice local (por exemplo via docker/compose)
curl -i http://localhost:8000/health

# Usando um trace fixo
curl -i -H "X-HUBLE-TRACE-ID: 4a750618-2ad1-494f-9142-bbe0a6e55874" \
  http://localhost:8000/health

4) Logs com huble_trace_id

Ao chamar setup_core(), a lib instala um filtro no root logger que injeta huble_trace_id em todos os registros.
Você pode referenciar %(huble_trace_id)s no seu formatter:

Exemplo (Django settings.py)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "%(asctime)s %(levelname)s trace=%(huble_trace_id)s %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "console"},
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}


Não precisa declarar o filtro aqui; o setup_core() já o adiciona programaticamente no root logger.

5) Outbound HTTP (httpx / requests)

Chamou enable_clients()? Então toda chamada cliente sai com o header X-HUBLE-TRACE-ID do contexto atual automaticamente.

import httpx
from tracker.huble.core import get_current_trace_id

async def call_upstream():
    async with httpx.AsyncClient() as c:
        r = await c.get("http://service/internal")
        # O header X-HUBLE-TRACE-ID foi enviado automaticamente


Mesma ideia para requests:

import requests

def call_upstream_sync():
    s = requests.Session()
    r = s.get("http://service/internal")

6) Dicas e troubleshooting

Django 400 / DisallowedHost: adicione o hostname do container em ALLOWED_HOSTS (ou * em dev).

Quer ver o header no response? Ele sempre é adicionado; rode curl -i ... e procure X-HUBLE-TRACE-ID.

Header fixo para teste: gere um UUID v4 e envie:

curl -i -H "X-HUBLE-TRACE-ID: 4a750618-2ad1-494f-9142-bbe0a6e55874" http://...
