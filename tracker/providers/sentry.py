import logging
from dataclasses import dataclass
from typing import Dict, Optional, cast

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from ..dtos import TrackerException, TrackerMessage
from ..interfaces import ITrackerHandlerException, ITrackerHandlerMessage
from ..types import Contexts, JSONFields, Tags


class SentryCore:
    @dataclass
    class SentryConfig:
        dsn: str
        environment: str
        traces_sample_rate: Optional[float] = None

    def __init__(self, config: SentryConfig):
        sentry_logging_integration = LoggingIntegration(  # pragma: no mutate
            level=logging.DEBUG,
            event_level=None,
        )

        sentry_sdk.init(
            dsn=config.dsn,
            environment=config.environment,
            integrations=[sentry_logging_integration],
            traces_sample_rate=config.traces_sample_rate,
            enable_tracing=config.traces_sample_rate is not None
            and config.traces_sample_rate > 0,
        )

    def set_tags(self, tags: Tags):
        for key, value in tags.items():
            sentry_sdk.set_tag(key, value)

    def set_contexts(self, contexts: Contexts):
        for key, value in contexts.items():
            value = cast(Dict[str, JSONFields], value)  # pragma: no mutate
            sentry_sdk.set_context(key, value)

    def capture_exception(self, exception: Exception):
        sentry_sdk.capture_exception(exception)

    def capture_message(self, message: str):
        sentry_sdk.capture_message(message)


class SentryMessageHandler(ITrackerHandlerMessage):
    def __init__(self, sentry: SentryCore):
        self.sentry = sentry

    def set_tags(self, tags: Tags):
        self.sentry.set_tags(tags)

    def set_contexts(self, contexts: Contexts):
        self.sentry.set_contexts(contexts)

    def capture_message(self, tracker_message: TrackerMessage):
        if tracker_message.tags:
            self.sentry.set_tags(tracker_message.tags)

        if tracker_message.contexts:
            self.sentry.set_contexts(tracker_message.contexts)

        self.sentry.capture_message(tracker_message.message.value)


class SentryExceptionHandler(ITrackerHandlerException):
    def __init__(self, sentry: SentryCore):
        self.sentry = sentry

    def set_tags(self, tags: Tags):
        self.sentry.set_tags(tags)

    def set_contexts(self, contexts: Contexts):
        self.sentry.set_contexts(contexts)

    def capture_exception(self, tracker_exception: TrackerException):
        if tracker_exception.tags:
            self.sentry.set_tags(tracker_exception.tags)

        if tracker_exception.contexts:
            self.sentry.set_contexts(tracker_exception.contexts)

        self.sentry.capture_exception(tracker_exception.exception)
