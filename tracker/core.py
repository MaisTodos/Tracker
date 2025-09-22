import logging
from typing import List, Optional

from .dtos import TrackerEvent, TrackerException, TrackerMessage
from .interfaces import (
    ITrackerHandlerEvent,
    ITrackerHandlerException,
    ITrackerHandlerMessage,
)
from .providers.redis import redis_exception_handler_factory
from .types import Contexts, Tags

logger = logging.getLogger(__name__)


class Tracker:
    def __init__(
        self,
        message_handlers: Optional[List[ITrackerHandlerMessage]] = None,
        exception_handlers: Optional[List[ITrackerHandlerException]] = None,
        event_handlers: Optional[List[ITrackerHandlerEvent]] = None,
    ):
        self.__message_handlers = message_handlers or []
        self.__exception_handlers = exception_handlers or []
        self.__event_handlers = event_handlers or []
        self.__exception_handlers.append(redis_exception_handler_factory())

    def set_tags(self, tags: Tags):
        handlers = (
            self.__event_handlers + self.__exception_handlers + self.__message_handlers
        )

        for handler in handlers:
            try:
                handler.set_tags(tags)
            except Exception as e:
                logger.error(f"Error setting tags for handler {handler}: {e}")

    def set_contexts(self, contexts: Contexts):
        handlers = (
            self.__event_handlers + self.__exception_handlers + self.__message_handlers
        )

        for handler in handlers:
            try:
                handler.set_contexts(contexts)
            except Exception as e:
                logger.error(f"Error setting contexts for handler {handler}: {e}")

    def emit_exception(self, tracker_exception: TrackerException):
        for handler in self.__exception_handlers:
            try:
                handler.capture_exception(tracker_exception)
            except Exception as e:
                logger.error(f"Error emitting exception for handler {handler}: {e}")

    def emit_message(self, tracker_message: TrackerMessage):
        for handler in self.__message_handlers:
            try:
                handler.capture_message(tracker_message)
            except Exception as e:
                logger.error(f"Error emitting message for handler {handler}: {e}")

    def emit_event(self, tracker_event: TrackerEvent):
        for handler in self.__event_handlers:
            try:
                handler.capture_event(tracker_event)
            except Exception as e:
                logger.error(f"Error emitting event for handler {handler}: {e}")
