import json
import logging
import os
from dataclasses import dataclass
from typing import Optional

import redis

from ..dtos import TrackerException, TrackerMessage
from ..interfaces import ITrackerHandlerException, ITrackerHandlerMessage
from ..types import Contexts, Tags

logger = logging.getLogger(__name__)


class RedisPubCore:
    @dataclass
    class RedisConfig:
        channel: str = "tracker-exceptions"
        url: Optional[str] = "redis://localhost:6379/0"

    def init(
        self,
        config: Optional["RedisConfig"] = None,
        client: Optional["redis.Redis"] = None,
    ):
        self.config = config or self.RedisConfig()

        if client is not None:
            self._client = client
        else:
            try:
                self._client = redis.from_url(self.config.url)
                self._client.ping()
            except Exception:
                self._client = None

    def set_tags(self, tags: Tags):  # no-op for Redis
        return

    def set_contexts(self, contexts: Contexts):  # no-op for Redis
        return

    def capture_exception(self, exception: Exception):
        if exception is None:
            return

        exception_data = {
            "exception": str(exception),
            "type": exception.__class__.__name__,
        }
        self._publish(exception_data)

    def capture_message(self, message: str):
        if not message:
            return

        message_data = {"message": message}
        self._publish(message_data)

    def _publish(self, payload: dict):
        if self._client is None:
            return False

        self._client.publish(self.config.channel, json.dumps(payload))


class RedisMessageHandler(ITrackerHandlerMessage):
    def __init__(self, redis_pub: RedisPubCore):
        self.redis_pub = redis_pub

    def set_tags(self, tags: Tags):
        if tags is not None:
            self.redis_pub.set_tags(tags)

    def set_contexts(self, contexts: Contexts):
        if contexts is not None:
            self.redis_pub.set_contexts(contexts)

    def capture_message(self, tracker_message: TrackerMessage):
        if tracker_message.tags is not None:
            self.redis_pub.set_tags(tracker_message.tags)
        if tracker_message.contexts is not None:
            self.redis_pub.set_contexts(tracker_message.contexts)

        self.redis_pub.capture_message(tracker_message.message.value)


class RedisExceptionHandler(ITrackerHandlerException):
    def __init__(self, redis_pub: RedisPubCore):
        self.redis_pub = redis_pub

    def set_tags(self, tags: Tags):
        if tags is not None:
            self.redis_pub.set_tags(tags)

    def set_contexts(self, contexts: Contexts):
        if contexts is not None:
            self.redis_pub.set_contexts(contexts)

    def capture_exception(self, tracker_exception: TrackerException):
        if tracker_exception.tags is not None:
            self.redis_pub.set_tags(tracker_exception.tags)
        if tracker_exception.contexts is not None:
            self.redis_pub.set_contexts(tracker_exception.contexts)

        self.redis_pub.capture_exception(tracker_exception.exception)


def redis_exception_handler_factory() -> RedisExceptionHandler:
    redis_pub = RedisPubCore()
    redis_pub.init()
    return RedisExceptionHandler(redis_pub)
