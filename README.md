# Tracker

Uma biblioteca modular e extensível para rastreamento de eventos, mensagens e exceções.

## Instalação

### Como utilizar no teu projeto?
Hoje a biblioteca não está publicada no PyPI e não pretendemos publicar tão cedo.
Por enquanto, você pode fazer referência pelo repositório GitHub:

#### Exemplo utilizando Poetry:
```bash
poetry add git+https://github.com/MaisTodos/Tracker.git
```

## Configuração Inicial

A biblioteca agora utiliza uma arquitetura baseada em handlers, permitindo configurar múltiplos provedores simultaneamente.

### Configuração

```python
from tracker import (
    Tracker,
    SentryCore,
    SentryExceptionHandler,
    SentryMessageHandler,
    LoggerCore,
    LoggerExceptionHandler,
    LoggerMessageHandler,
)

sentry_core = SentryCore(
    SentryCore.SentryConfig(
        dsn="YOUR_SENTRY_DSN",
        environment="production",
        trace_sample_rate=1.0,
    )
)
sentry_exception_handler = SentryExceptionHandler(sentry_core)
sentry_message_handler = SentryMessageHandler(sentry_core)

logger_core = LoggerCore(LoggerCore.LoggerConfig())
logger_exception_handler = LoggerExceptionHandler(logger_core)
logger_message_handler = LoggerMessageHandler(logger_core)

tracker = Tracker(
    exception_handlers=[sentry_exception_handler, logger_exception_handler],
    message_handlers=[sentry_message_handler, logger_message_handler],
)
```

### MixPanel (eventos)

O provedor MixPanel implementa apenas o handler de eventos (`event_handlers`). Requer o extra
`mixpanel` instalado (`pip install mixpanel`).

```python
from tracker import Tracker, MixPanelHandlerEvent

mix_panel_handler = MixPanelHandlerEvent(
    config=MixPanelHandlerEvent.MixPanelConfig(
        project_token="YOUR_PROJECT_TOKEN",
        service_name="auth-service",
    )
)

tracker = Tracker(event_handlers=[mix_panel_handler])
```

O `distinct_id` do evento é resolvido a partir das tags `distinct_id`, `id` ou `user_id` (nessa
ordem). Quando nenhuma está presente, usa-se `"{service_name}-server"`. Cada evento recebe ainda
um atributo `source` igual a `"{service_name}-server"`.

> **Observação:** Logger e MixPanel **não** aplicam tags/contextos globais
> (`tracker.set_tags`/`set_contexts`) — essas chamadas apenas emitem um log `debug`. Apenas o
> Sentry honra tags/contextos globais. Para Logger e MixPanel, informe as tags/contextos por
> evento/mensagem/exceção.

## Uso

O Tracker é orientado a tipos à dados a emitir: exceções, mensagens e eventos. Para mensagens e eventos, é necessário definir enums.

### Rastreamento de Exceções

```python
from tracker import TrackerException
from enum import Enum

class ErrorTags(Enum):
    CRITICAL = "critical"
    WARNING = "warning"

try:
    1 / 0
except ZeroDivisionError as error:
    tracker.emit_exception(
        TrackerException(
            exception=error,
            tags={"severity": ErrorTags.CRITICAL.value},
            contexts={
                "operation": {
                    "type": "division",
                    "operands": [1, 0]
                }
            }
        )
    )
```

### Enviando Mensagens

```python
from tracker import TrackerMessage
from enum import Enum

class CheckoutEvents(Enum):
    CHECKOUT_SUCCESS = "checkout_success"

message = TrackerMessage(
    message=CheckoutEvents.CHECKOUT_SUCCESS,
    tags={"partner": "premium"},
    contexts={
        "user_info": {
            "id": "12345",
            "email": "usuario@exemplo.com",
            "value": 250.75
        }
    }
)
tracker.emit_message(message)
```

### Enviando Eventos

```python
from tracker import TrackerEvent
from enum import Enum

class SystemEvents(Enum):
    STARTUP = "system_startup"
    SHUTDOWN = "system_shutdown"
    HEALTH_CHECK = "health_check"

# Evento do sistema
event = TrackerEvent(
    event=SystemEvents.STARTUP,
    tags={"version": "1.0.0"},
)
tracker.emit_event(event)
```

## Configurando Tags e Contextos Globais

O tracker permite configurar tags e contextos que serão aplicados automaticamente a todos os eventos, mensagens e exceções enviados pelos handlers.

```python
# Configurar tags globais
tracker.set_tags({
    "service": "user-service",
    "version": "v1.2.3",
    "environment": "production"
})

# Configurar contextos globais
tracker.set_contexts({
    "app_info": {
        "version": "1.2.3",
        "build_number": "456"
    },
    "server": {
        "region": "us-east-1",
        "instance_id": "i-1234567890abcdef0"
    }
})
```


### Exemplo Completo

```python
from tracker import (
    Tracker, TrackerMessage, TrackerException, TrackerEvent,
    SentryCore, SentryExceptionHandler, SentryMessageHandler,
    LoggerCore, LoggerExceptionHandler, LoggerMessageHandler,
)
from enum import Enum

# Definir enums
class UserEvents(Enum):
    LOGIN = "user_login"
    LOGOUT = "user_logout"

class UserType(Enum):
    ADMIN = "admin"
    REGULAR = "regular"

# Configurar provedores
sentry_core = SentryCore(SentryCore.SentryConfig(dsn="YOUR_DSN"))
logger_core = LoggerCore(LoggerCore.LoggerConfig())

# Criar tracker
tracker = Tracker(
    message_handlers=[
        SentryMessageHandler(sentry_core),
        LoggerMessageHandler(logger_core),
    ],
    exception_handlers=[
        SentryExceptionHandler(sentry_core),
        LoggerExceptionHandler(logger_core),
    ]
)

# Configurar dados globais
tracker.set_tags({"service": "auth-service"})
tracker.set_contexts({
    "app": {"version": "1.0.0"}
})

# Usar o tracker
try:
    # Simular login
    message = TrackerMessage(
        message=UserEvents.LOGIN,
        tags={"user_type": UserType.ADMIN.value},
        contexts={
            "user": {"id": "123", "email": "admin@example.com"}
        }
    )
    tracker.emit_message(message)
    
    # Simular erro
    raise ValueError("Erro de exemplo")
    
except ValueError as e:
    exception = TrackerException(
        exception=e,
        tags={"severity": "medium"},
        contexts={"operation": {"type": "authentication"}}
    )
    tracker.emit_exception(exception)
```

## Contribuição e Desenvolvimento

### Instalação
```bash
poetry install --all-extras
```

### Executar Testes

```bash
# Executar todos os testes
make test

# Executar com cobertura
make coverage

# Testes de mutação
make mutation
```

### Formatação e Linting

```bash
# Formatação automática
make black
make isort
```

### Empacotamento (pyproject.toml + setup.cfg)

O projeto mantém os metadados de empacotamento em **dois** lugares, de propósito:

- **`pyproject.toml`** (`[tool.poetry]`) — fonte usada pelo Poetry/PEP 517. O build normal
  (`poetry build`, `poetry install`, `poetry add git+https://.../Tracker.git`) usa o backend
  `poetry.core.masonry.api` declarado em `[build-system]` e **ignora** o `setup.py`/`setup.cfg`.
- **`setup.py` + `setup.cfg`** — existem **apenas** para compatibilidade com o **Chalice**.
  Ao montar a Lambda layer (`automatic_layer: "true"`), o Chalice baixa a árvore de fontes de
  cada dependência git e extrai name/version rodando `python setup.py egg_info`. Como o Tracker
  é um pacote poetry-core puro, sem esses arquivos ele falharia com
  `UnsupportedPackageError: Unable to retrieve name/version for package: tracker`.
  O `setup.py` é só um stub (`from setuptools import setup; setup()`) que dispara o setuptools,
  que por sua vez lê os metadados do `setup.cfg`.

> ⚠️ **Ao gerar um upgrade, atualize os dois arquivos em paralelo.** Os campos abaixo estão
> duplicados e precisam ficar sempre iguais, senão o Chalice e o Poetry passam a enxergar
> metadados diferentes:
>
> | O que muda | `pyproject.toml` (`[tool.poetry]`) | `setup.cfg` |
> | --- | --- | --- |
> | Versão do release | `version` | `[metadata] version` |
> | Versão do Python suportada | `[tool.poetry.dependencies] python` | `[options] python_requires` |
> | Extra `sentry` / novas deps | `[tool.poetry.dependencies]` + `[tool.poetry.extras]` | `[options.extras_require]` / `[options] install_requires` |
> | Novo (sub)pacote | `packages = [{ include = "..." }]` | `[options] packages` |

**Checklist de bump de versão (ex.: 0.5.0 → 0.6.0):**

1. Atualize `version` em `pyproject.toml` **e** `[metadata] version` em `setup.cfg` para o
   mesmo valor.
2. Se mexeu em dependências ou no `python`, replique a mudança nas duas tabelas correspondentes
   (ver tabela acima).
3. Valide que ambos os caminhos de build enxergam os mesmos metadados:
   ```bash
   # Caminho do Chalice — deve imprimir o Name/Version novos:
   python setup.py egg_info && grep -E '^(Name|Version):' tracker.egg-info/PKG-INFO
   rm -rf tracker.egg-info                 # artefato temporário (já está no .gitignore)

   # Caminho do Poetry — deve gerar tracker-<versão>.{tar.gz,whl}:
   poetry build && ls dist/ && rm -rf dist/
   ```
4. Crie a tag correspondente (`vX.Y.Z`) ao publicar o release.

> `setup.py egg_info` precisa do `setuptools` instalado no ambiente (o venv poetry-core puro
> não o traz). No CI/Chalice ele já está disponível; localmente, rode num ambiente com
> `setuptools` (ex.: `pip install setuptools` num venv separado).

## Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

### Diretrizes

- Mantenha a cobertura de testes acima de 100%
- Mantenha testes de mutação em 100%
- Siga as convenções de código (Black + isort)
- Ao bumpar versão ou mexer em dependências, atualize `pyproject.toml` **e** `setup.cfg` em
  paralelo (ver [Empacotamento](#empacotamento-pyprojecttoml--setupcfg))
