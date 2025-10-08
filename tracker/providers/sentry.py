import logging
from dataclasses import dataclass
from typing import Annotated, Dict, Optional, cast

from ..dtos import TrackerException, TrackerMessage
from ..interfaces import ITrackerHandlerException, ITrackerHandlerMessage
from ..types import Contexts, JSONFields, Tags


class SentryCore:
    @dataclass
    class SentryConfig:
        dsn: str
        environment: str
        use_otel: Annotated[
            bool, "Use Sentry with OpenTelemetry if available, else fallback to Sentry"
        ] = True
        traces_sample_rate: Optional[float] = None
        before_send_function: Optional[callable] = None

    def __init__(self, config: SentryConfig):
        try:
            import sentry_sdk
            from sentry_sdk.integrations.logging import LoggingIntegration

        except ImportError as e:
            raise ImportError(
                "sentry-sdk is required to use Sentry with Tracker. Please install it via 'pip install sentry-sdk'."
            ) from e

        self.sentry_sdk = sentry_sdk

        sentry_logging_integration = LoggingIntegration(  # pragma: no mutate
            level=logging.DEBUG,
            event_level=None,
        )

        otel_initialized = False  # pragma: no mutate
        if config.use_otel:
            otel_initialized = self.__initialize_otel()

        self.sentry_sdk.init(
            dsn=config.dsn,
            environment=config.environment,
            integrations=[sentry_logging_integration],
            traces_sample_rate=config.traces_sample_rate,
            before_send=config.before_send_function,
            instrumenter="otel" if otel_initialized else "sentry",
        )

    def __initialize_otel(self) -> bool:
        try:
            from opentelemetry import trace
            from opentelemetry.propagate import set_global_textmap
            from sentry_sdk.integrations.opentelemetry import (
                SentryPropagator,
                SentrySpanProcessor,
            )
        except ImportError:
            return False

        # Attach Sentry to existing OpenTelemetry setup
        provider = trace.get_tracer_provider()
        provider.add_span_processor(SentrySpanProcessor())
        set_global_textmap(SentryPropagator())
        return True

    def set_tags(self, tags: Tags):
        for key, value in tags.items():
            self.sentry_sdk.set_tag(key, value)

    def set_contexts(self, contexts: Contexts):
        for key, value in contexts.items():
            value = cast(Dict[str, JSONFields], value)  # pragma: no mutate
            self.sentry_sdk.set_context(key, value)

    def capture_exception(self, exception: Exception):
        self.sentry_sdk.capture_exception(exception)

    def capture_message(self, message: str):
        self.sentry_sdk.capture_message(message)


class SentryMessageHandler(ITrackerHandlerMessage):
    def __init__(self, sentry_core: SentryCore):
        self.sentry_core = sentry_core

    def set_tags(self, tags: Tags):
        self.sentry_core.set_tags(tags)

    def set_contexts(self, contexts: Contexts):
        self.sentry_core.set_contexts(contexts)

    def capture_message(self, tracker_message: TrackerMessage):
        if tracker_message.tags:
            self.sentry_core.set_tags(tracker_message.tags)

        if tracker_message.contexts:
            self.sentry_core.set_contexts(tracker_message.contexts)

        self.sentry_core.capture_message(tracker_message.message.value)


class SentryExceptionHandler(ITrackerHandlerException):
    def __init__(self, sentry_core: SentryCore):
        self.sentry_core = sentry_core

    def set_tags(self, tags: Tags):
        self.sentry_core.set_tags(tags)

    def set_contexts(self, contexts: Contexts):
        self.sentry_core.set_contexts(contexts)

    def capture_exception(self, tracker_exception: TrackerException):
        if tracker_exception.tags:
            self.sentry_core.set_tags(tracker_exception.tags)

        if tracker_exception.contexts:
            self.sentry_core.set_contexts(tracker_exception.contexts)

        self.sentry_core.capture_exception(tracker_exception.exception)
