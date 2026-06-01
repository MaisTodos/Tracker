import logging
from dataclasses import dataclass
from typing import Optional

from ..dtos import TrackerEvent, TrackerException, TrackerMessage
from ..interfaces import (
    ITrackerHandlerEvent,
    ITrackerHandlerException,
    ITrackerHandlerMessage,
)
from ..types import Contexts, Tags


class LoggerCore:
    @dataclass
    class LoggerConfig:
        logger_handler: Optional[logging.Handler] = None

    _SET_TAGS_MESSAGE: str = (
        "LoggerCore does not support global 'set_tags', ignoring "
        "(pass tags per message/event/exception instead)."
    )
    _SET_CONTEXTS_MESSAGE: str = (
        "LoggerCore does not support global 'set_contexts', ignoring "
        "(pass contexts per message/event/exception instead)."
    )

    def __init__(self, config: LoggerConfig):
        self.logger = logging.getLogger("Tracker.LoggerCore")

        if len(self.logger.handlers):
            # Avoid adding multiple handlers
            return

        if config.logger_handler:
            self.logger.addHandler(config.logger_handler)
        else:
            handler = logging.StreamHandler()
            self.logger.addHandler(handler)

    def set_tags(self, tags: Tags):
        self.logger.debug(self._SET_TAGS_MESSAGE)

    def set_contexts(self, contexts: Contexts):
        self.logger.debug(self._SET_CONTEXTS_MESSAGE)


class LoggerMessageHandler(ITrackerHandlerMessage):
    def __init__(self, core: LoggerCore):
        self.core = core

    def set_tags(self, tags: Tags):
        self.core.set_tags(tags)

    def set_contexts(self, contexts: Contexts):
        self.core.set_contexts(contexts)

    def capture_message(self, tracker_message: TrackerMessage):
        extra = {"tags": {}, "contexts": {}}

        if tracker_message.tags:
            extra["tags"].update(tracker_message.tags)

        if tracker_message.contexts:
            extra["contexts"].update(tracker_message.contexts)

        self.core.logger.info(tracker_message.message.value, extra=extra)


class LoggerExceptionHandler(ITrackerHandlerException):
    def __init__(self, core: LoggerCore):
        self.core = core

    def set_tags(self, tags: Tags):
        self.core.set_tags(tags)

    def set_contexts(self, contexts: Contexts):
        self.core.set_contexts(contexts)

    def capture_exception(self, tracker_exception: TrackerException):
        extra = {"tags": {}, "contexts": {}}

        if tracker_exception.tags:
            extra["tags"].update(tracker_exception.tags)

        if tracker_exception.contexts:
            extra["contexts"].update(tracker_exception.contexts)

        self.core.logger.error(
            tracker_exception.exception.__class__.__name__,
            exc_info=tracker_exception.exception,
            extra=extra,
        )


class LoggerEventHandler(ITrackerHandlerEvent):
    def __init__(self, core: LoggerCore):
        self.core = core

    def set_tags(self, tags: Tags):
        self.core.set_tags(tags)

    def set_contexts(self, contexts: Contexts):
        self.core.set_contexts(contexts)

    def capture_event(self, tracker_event: TrackerEvent):
        extra = {"tags": {}, "contexts": {}}

        if tracker_event.tags:
            extra["tags"].update(tracker_event.tags)

        if tracker_event.contexts:
            extra["contexts"].update(tracker_event.contexts)

        self.core.logger.info(tracker_event.event.value, extra=extra)
