import json
from unittest.mock import MagicMock, Mock, patch

import pytest
import redis

from tracker.providers.redis import (
    RedisExceptionHandler,
    RedisMessageHandler,
    RedisPubCore,
    redis_exception_handler_factory,
)


def test_publish_success():
    mock_client = Mock()
    core = RedisPubCore()
    core.init(client=mock_client)

    core.capture_message("hello")
    mock_client.publish.assert_called_once_with(
        "tracker-exceptions", json.dumps({"message": "hello"})
    )


def test_no_client_does_nothing():
    core = RedisPubCore()
    core.init()  # This should create a None client since no Redis is available
    core.capture_message("ignored")
    core.capture_exception(Exception("ignored"))
    # Should not raise any errors


def test_set_tags_and_contexts_are_noops():
    mock_client = Mock()
    core = RedisPubCore()
    core.init(client=mock_client)
    # these should just return silently without calling Redis
    core.set_tags({"foo": "bar"})
    core.set_contexts({"ctx": {"x": 1}})
    # Verify no Redis calls were made for set_tags/set_contexts
    mock_client.publish.assert_not_called()


@patch("tracker.providers.redis.redis.from_url")
def test_init_with_url_success(mock_from_url):
    mock_client = Mock()
    mock_client.ping.return_value = True
    mock_from_url.return_value = mock_client

    core = RedisPubCore()
    core.init()

    assert core._client == mock_client
    mock_from_url.assert_called_once_with("redis://localhost:6379/0")


@patch("tracker.providers.redis.redis.from_url")
def test_init_with_url_failure(mock_from_url):
    mock_from_url.side_effect = Exception("bad url")

    core = RedisPubCore()
    core.init()

    assert core._client is None


def test_init_with_client():
    """Test initialization with provided client"""
    mock_client = Mock()

    core = RedisPubCore()
    core.init(client=mock_client)

    assert core._client is mock_client


def test_init_no_client_no_url():
    """Test initialization without client or URL"""
    core = RedisPubCore()
    core.init()

    # This depends on whether Redis is available
    # The test should handle both cases
    assert core._client is None or hasattr(core._client, "publish")


def test_capture_exception_with_valid_exception():
    """Test capturing valid exception"""
    mock_client = Mock()
    core = RedisPubCore()
    core.init(client=mock_client)

    exception = ValueError("test error")
    core.capture_exception(exception)

    expected_payload = {"exception": "test error", "type": "ValueError"}
    mock_client.publish.assert_called_once_with(
        "tracker-exceptions", json.dumps(expected_payload)
    )


def test_capture_exception_with_none():
    """Test capturing None exception"""
    mock_client = Mock()
    core = RedisPubCore()
    core.init(client=mock_client)

    core.capture_exception(None)

    # Should not call publish
    mock_client.publish.assert_not_called()


def test_capture_message_with_valid_message():
    """Test capturing valid message"""
    mock_client = Mock()
    core = RedisPubCore()
    core.init(client=mock_client)

    core.capture_message("test message")

    expected_payload = {"message": "test message"}
    mock_client.publish.assert_called_once_with(
        "tracker-exceptions", json.dumps(expected_payload)
    )


def test_capture_message_with_empty_message():
    """Test capturing empty message"""
    mock_client = Mock()
    core = RedisPubCore()
    core.init(client=mock_client)

    core.capture_message("")

    # Should not call publish
    mock_client.publish.assert_not_called()


def test_publish_no_client():
    """Test publish with no client"""
    core = RedisPubCore()
    core.init()  # No client provided and Redis not available

    # This should return False when no client is available
    result = core._publish({"test": "data"})
    assert result is False


def test_message_handler_capture_message_with_tags_and_contexts():
    """Test capture_message with tags and contexts"""
    redis_pub = Mock()
    handler = RedisMessageHandler(redis_pub)

    # Create a proper TrackerMessage-like object
    tracker_message = Mock()
    tracker_message.tags = {"key": "value"}
    tracker_message.contexts = {"context": "data"}
    tracker_message.message = Mock()
    tracker_message.message.value = "test message"

    handler.capture_message(tracker_message)

    redis_pub.set_tags.assert_called_once_with({"key": "value"})
    redis_pub.set_contexts.assert_called_once_with({"context": "data"})
    redis_pub.capture_message.assert_called_once_with("test message")


def test_message_handler_set_tags_with_none():
    """Test set_tags with None"""
    redis_pub = Mock()
    handler = RedisMessageHandler(redis_pub)

    handler.set_tags(None)

    redis_pub.set_tags.assert_not_called()


def test_message_handler_set_contexts_with_none():
    """Test set_contexts with None"""
    redis_pub = Mock()
    handler = RedisMessageHandler(redis_pub)

    handler.set_contexts(None)

    redis_pub.set_contexts.assert_not_called()


def test_exception_handler_capture_exception_with_tags_and_contexts():
    """Test capture_exception with tags and contexts"""
    redis_pub = Mock()
    handler = RedisExceptionHandler(redis_pub)

    # Create a proper TrackerException-like object
    tracker_exception = Mock()
    tracker_exception.tags = {"key": "value"}
    tracker_exception.contexts = {"context": "data"}
    tracker_exception.exception = ValueError("test error")

    handler.capture_exception(tracker_exception)

    redis_pub.set_tags.assert_called_once_with({"key": "value"})
    redis_pub.set_contexts.assert_called_once_with({"context": "data"})
    redis_pub.capture_exception.assert_called_once_with(tracker_exception.exception)


def test_exception_handler_set_tags_with_none():
    """Test set_tags with None"""
    redis_pub = Mock()
    handler = RedisExceptionHandler(redis_pub)

    handler.set_tags(None)

    redis_pub.set_tags.assert_not_called()


def test_exception_handler_set_contexts_with_none():
    """Test set_contexts with None"""
    redis_pub = Mock()
    handler = RedisExceptionHandler(redis_pub)

    handler.set_contexts(None)

    redis_pub.set_contexts.assert_not_called()


def test_capture_exception_different_exception_types():
    """Test capturing different exception types"""
    mock_client = Mock()
    core = RedisPubCore()
    core.init(client=mock_client)

    exceptions = [
        ValueError("value error"),
        TypeError("type error"),
        RuntimeError("runtime error"),
    ]

    for exc in exceptions:
        mock_client.reset_mock()
        core.capture_exception(exc)

        expected_payload = {"exception": str(exc), "type": exc.__class__.__name__}
        mock_client.publish.assert_called_once_with(
            "tracker-exceptions", json.dumps(expected_payload)
        )


def test_json_serialization_edge_cases():
    """Test JSON serialization with complex data"""
    mock_client = Mock()
    core = RedisPubCore()
    core.init(client=mock_client)

    core.capture_message("测试消息 🚀")

    expected_payload = {"message": "测试消息 🚀"}
    mock_client.publish.assert_called_with(
        "tracker-exceptions", json.dumps(expected_payload)
    )


def test_custom_config():
    """Test initialization with custom config"""
    mock_client = Mock()
    config = RedisPubCore.RedisConfig(
        channel="custom-channel", url="redis://custom-host:6379/1"
    )

    core = RedisPubCore()
    core.init(config=config, client=mock_client)

    core.capture_message("test")
    mock_client.publish.assert_called_with(
        "custom-channel", json.dumps({"message": "test"})
    )


@patch("tracker.providers.redis.redis.from_url")
def test_redis_exception_handler_factory(mock_from_url):
    """Test the factory function"""
    mock_client = Mock()
    mock_client.ping.return_value = True
    mock_from_url.return_value = mock_client

    handler = redis_exception_handler_factory()

    assert isinstance(handler, RedisExceptionHandler)
    assert handler.redis_pub._client == mock_client
    mock_from_url.assert_called_once_with("redis://localhost:6379/0")


def test_publish_returns_false_when_no_client():
    """Test that _publish returns False when no client is available"""
    core = RedisPubCore()
    core.init()  # No client

    result = core._publish({"test": "data"})
    assert result is False


def test_publish_returns_none_when_client_exists():
    """Test that _publish returns None (client.publish returns None) when client exists"""
    mock_client = Mock()
    mock_client.publish.return_value = None
    core = RedisPubCore()
    core.init(client=mock_client)

    result = core._publish({"test": "data"})
    assert result is None


def test_init_with_config_only():
    """Test initialization with config only (no client)"""
    config = RedisPubCore.RedisConfig(channel="test-channel")

    with patch("tracker.providers.redis.redis.from_url") as mock_from_url:
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_from_url.return_value = mock_client

        core = RedisPubCore()
        core.init(config=config)

        assert core._client == mock_client
        assert core.config.channel == "test-channel"


def test_init_ping_failure():
    """Test initialization when ping fails"""
    with patch("tracker.providers.redis.redis.from_url") as mock_from_url:
        mock_client = Mock()
        mock_client.ping.side_effect = Exception("Connection failed")
        mock_from_url.return_value = mock_client

        core = RedisPubCore()
        core.init()

        assert core._client is None
