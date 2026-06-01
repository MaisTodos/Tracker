import logging
from unittest.mock import MagicMock

from tracker.providers.logger import LoggerMessageHandler


def test_logger_message_handler_delegates_set_tags_and_contexts(logger_core):
    logger_core.set_tags = MagicMock()
    logger_core.set_contexts = MagicMock()
    handler = LoggerMessageHandler(logger_core)

    handler.set_tags({"a": "b"})
    handler.set_contexts({"c": {"d": "e"}})

    logger_core.set_tags.assert_called_once_with({"a": "b"})
    logger_core.set_contexts.assert_called_once_with({"c": {"d": "e"}})


def test_logger_message_handler_capture(logger_core, tracker_message, caplog):
    message_handler = LoggerMessageHandler(logger_core)

    message_handler.set_tags({"global_tag": "global_value"})
    message_handler.set_contexts({"global_context": "global_value"})

    with caplog.at_level(logging.INFO):
        message_handler.capture_message(tracker_message)

    assert len(caplog.records) == 1

    log_record = caplog.records[0]
    assert log_record.levelname == "INFO"
    assert log_record.message == "test_message"
    assert log_record.tags == {}
    assert log_record.contexts == {}


def test_logger_message_handler_capture_with_local_tags_and_contexts(
    logger_core, tracker_message, caplog
):
    message_handler = LoggerMessageHandler(logger_core)

    message_handler.set_tags({"global_tag": "global_value"})
    message_handler.set_contexts({"global_context": "global_value"})

    tracker_message.tags = {"local_tag": "local_value"}
    tracker_message.contexts = {"local_context": "local_value"}

    with caplog.at_level(logging.INFO):
        message_handler.capture_message(tracker_message)

    assert len(caplog.records) == 1

    log_record = caplog.records[0]
    assert log_record.levelname == "INFO"
    assert log_record.message == "test_message"
    assert log_record.tags == {"local_tag": "local_value"}
    assert log_record.contexts == {"local_context": "local_value"}
