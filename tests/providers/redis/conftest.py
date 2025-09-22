from unittest.mock import Mock

import pytest

from tracker.dtos import TrackerException, TrackerMessage
from tracker.providers.redis import RedisPubCore


@pytest.fixture
def redis_core_mock():
    return Mock(spec=RedisPubCore)


@pytest.fixture
def tracker_exception():
    exc = Exception("boom")
    return TrackerException(
        exception=exc,
        tags={"tag1": "value1"},
        contexts={"ctx1": {"key": "val"}},
    )


@pytest.fixture
def tracker_message():
    class DummyMessage:
        value = "hello world"

    return TrackerMessage(
        message=DummyMessage(),
        tags={"tag1": "value1"},
        contexts={"ctx1": {"key": "val"}},
    )
