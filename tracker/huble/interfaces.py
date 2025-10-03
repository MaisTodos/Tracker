from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional, Iterable

class IFrameworkAdapter(ABC):
    @abstractmethod
    def attach(
        self,
        app: Any,
        *,
        log_request_response: bool = False,
        logger: Optional[Any] = None,
        redact_headers: Optional[Iterable[str]] = None,
    ) -> Any: ...

class IHttpClientAdapter(ABC):
    @abstractmethod
    def patch(self) -> None: ...
