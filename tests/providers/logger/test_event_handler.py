import logging
from unittest.mock import MagicMock

from tracker.providers.logger import LoggerEventHandler


def test_logger_event_handler_delegates_set_tags_and_contexts(logger_core):
    logger_core.set_tags = MagicMock()
    logger_core.set_contexts = MagicMock()
    handler = LoggerEventHandler(logger_core)

    handler.set_tags({"a": "b"})
    handler.set_contexts({"c": {"d": "e"}})

    logger_core.set_tags.assert_called_once_with({"a": "b"})
    logger_core.set_contexts.assert_called_once_with({"c": {"d": "e"}})


def test_logger_event_handler_capture(logger_core, tracker_event, caplog):
    event_handler = LoggerEventHandler(logger_core)

    event_handler.set_tags({"global_tag": "global_value"})
    event_handler.set_contexts({"global_context": "global_value"})

    with caplog.at_level(logging.INFO):
        event_handler.capture_event(tracker_event)

    assert len(caplog.records) == 1

    log_record = caplog.records[0]
    assert log_record.levelname == "INFO"
    assert log_record.message == "test_event"
    assert log_record.tags == {}
    assert log_record.contexts == {}


def test_logger_event_handler_capture_with_local_tags_and_contexts(
    logger_core, tracker_event, caplog
):
    event_handler = LoggerEventHandler(logger_core)

    event_handler.set_tags({"global_tag": "global_value"})
    event_handler.set_contexts({"global_context": "global_value"})

    tracker_event.tags = {"local_tag": "local_value"}
    tracker_event.contexts = {"local_context": "local_value"}

    with caplog.at_level(logging.INFO):
        event_handler.capture_event(tracker_event)

    assert len(caplog.records) == 1

    log_record = caplog.records[0]
    assert log_record.levelname == "INFO"
    assert log_record.message == "test_event"
    assert log_record.tags == {"local_tag": "local_value"}
    assert log_record.contexts == {"local_context": "local_value"}
