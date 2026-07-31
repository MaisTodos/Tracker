import hashlib
import hmac
import logging

import pytest

from tracker.core import Tracker


def test_hash_distinct_id_invalid_secret_length():
    with pytest.raises(ValueError) as err:
        Tracker.hash_distinct_id(value="12345678901", secret="a" * 16)

    assert (
        err.value.args[0]
        == "Error in secret length. Must be at least 32 characters long, got 16"
    )


def test_hash_distinct_id_different_values():
    secret = "a" * 32

    first = Tracker.hash_distinct_id(value="12345678901", secret=secret)
    second = Tracker.hash_distinct_id(value="98765432100", secret=secret)

    assert first != second


def test_hash_distinct_id_different_secrets():
    document = "12345678901"

    first = Tracker.hash_distinct_id(value=document, secret="a" * 32)
    second = Tracker.hash_distinct_id(value=document, secret="b" * 32)

    assert first != second


def test_hash_distinct_id_is_deterministic():
    document = "12345678901"
    document_with_mask = "123.456.789-01"
    secret = "a" * 32

    first = Tracker.hash_distinct_id(value=document, secret=secret)
    second = Tracker.hash_distinct_id(value=document, secret=secret)
    with_mask = Tracker.hash_distinct_id(value=document_with_mask, secret=secret)

    assert first == second == with_mask


def test_tracker_emit_without_handlers(
    tracker_message, tracker_exception, tracker_event
):
    tracker = Tracker()
    tracker.emit_event(tracker_event)
    tracker.emit_message(tracker_message)
    tracker.emit_exception(tracker_exception)


def test_tracker_set_tags_without_handlers():
    tracker = Tracker()
    tracker.set_tags({"key": "value"})


def test_tracker_set_contexts_without_handlers():
    tracker = Tracker()
    tracker.set_contexts({"context": {"detail": "info"}})


def test_tracker_emit_message(tracker_message, handlers_mocks):
    message_handler_one = handlers_mocks["message_handlers"][0]
    message_handler_two = handlers_mocks["message_handlers"][1]
    exception_handler = handlers_mocks["exception_handlers"][0]
    event_handler = handlers_mocks["event_handlers"][0]

    tracker = Tracker(
        message_handlers=[message_handler_one, message_handler_two],
        exception_handlers=[exception_handler],
        event_handlers=[event_handler],
    )

    tracker.emit_message(tracker_message)

    message_handler_one.capture_message.assert_called_once_with(tracker_message)
    message_handler_two.capture_message.assert_called_once_with(tracker_message)
    exception_handler.capture_exception.assert_not_called()
    event_handler.capture_event.assert_not_called()


def test_tracker_emit_exception(tracker_exception, handlers_mocks):
    exception_handler_one = handlers_mocks["exception_handlers"][0]
    exception_handler_two = handlers_mocks["exception_handlers"][1]
    event_handler = handlers_mocks["event_handlers"][0]
    message_handler = handlers_mocks["message_handlers"][0]

    tracker = Tracker(
        message_handlers=[message_handler],
        event_handlers=[event_handler],
        exception_handlers=[exception_handler_one, exception_handler_two],
    )

    tracker.emit_exception(tracker_exception)

    exception_handler_one.capture_exception.assert_called_once_with(tracker_exception)
    exception_handler_two.capture_exception.assert_called_once_with(tracker_exception)
    event_handler.capture_event.assert_not_called()
    message_handler.capture_message.assert_not_called()


def test_tracker_emit_event(tracker_event, handlers_mocks):
    event_handler_one = handlers_mocks["event_handlers"][0]
    event_handler_two = handlers_mocks["event_handlers"][1]
    message_handler = handlers_mocks["message_handlers"][0]
    exception_handler = handlers_mocks["exception_handlers"][0]

    tracker = Tracker(
        event_handlers=[event_handler_one, event_handler_two],
        message_handlers=[message_handler],
        exception_handlers=[exception_handler],
    )

    tracker.emit_event(tracker_event)

    event_handler_one.capture_event.assert_called_once_with(tracker_event)
    event_handler_two.capture_event.assert_called_once_with(tracker_event)
    message_handler.capture_message.assert_not_called()
    exception_handler.capture_exception.assert_not_called()


def test_tracker_emit_message_when_handler_raises(
    tracker_message, handlers_mocks, caplog
):
    message_handler_one = handlers_mocks["message_handlers"][0]
    message_handler_two = handlers_mocks["message_handlers"][1]
    message_handler_one.capture_message.side_effect = Exception("Handler Error")

    tracker = Tracker(message_handlers=[message_handler_one, message_handler_two])

    with caplog.at_level(logging.ERROR):
        tracker.emit_message(tracker_message)

    message_handler_one.capture_message.assert_called_once_with(tracker_message)
    message_handler_two.capture_message.assert_called_once_with(tracker_message)

    log_record = caplog.records[0]
    assert (
        log_record.message
        == f"Error emitting message for handler {message_handler_one}: Handler Error"
    )


def test_tracker_emit_exception_when_handler_raises(
    tracker_exception, handlers_mocks, caplog
):
    exception_handler_one = handlers_mocks["exception_handlers"][0]
    exception_handler_two = handlers_mocks["exception_handlers"][1]
    exception_handler_one.capture_exception.side_effect = Exception("Handler Error")

    tracker = Tracker(exception_handlers=[exception_handler_one, exception_handler_two])

    with caplog.at_level(logging.ERROR):
        tracker.emit_exception(tracker_exception)

    exception_handler_one.capture_exception.assert_called_once_with(tracker_exception)
    exception_handler_two.capture_exception.assert_called_once_with(tracker_exception)

    log_record = caplog.records[0]
    assert (
        log_record.message
        == f"Error emitting exception for handler {exception_handler_one}: Handler Error"
    )


def test_tracker_emit_event_when_handler_raises(tracker_event, handlers_mocks, caplog):
    event_handler_one = handlers_mocks["event_handlers"][0]
    event_handler_two = handlers_mocks["event_handlers"][1]
    event_handler_one.capture_event.side_effect = Exception("Handler Error")

    tracker = Tracker(event_handlers=[event_handler_one, event_handler_two])

    with caplog.at_level(logging.ERROR):
        tracker.emit_event(tracker_event)

    event_handler_one.capture_event.assert_called_once_with(tracker_event)
    event_handler_two.capture_event.assert_called_once_with(tracker_event)

    log_record = caplog.records[0]
    assert (
        log_record.message
        == f"Error emitting event for handler {event_handler_one}: Handler Error"
    )


def test_tracker_set_tags(handlers_mocks):
    message_handler = handlers_mocks["message_handlers"][0]
    exception_handler = handlers_mocks["exception_handlers"][0]
    event_handler = handlers_mocks["event_handlers"][0]

    tracker = Tracker(
        message_handlers=[message_handler],
        exception_handlers=[exception_handler],
        event_handlers=[event_handler],
    )

    tags = {"key": "value"}
    tracker.set_tags(tags)

    message_handler.set_tags.assert_called_once_with(tags)
    exception_handler.set_tags.assert_called_once_with(tags)
    event_handler.set_tags.assert_called_once_with(tags)


def test_tracker_set_tags_when_handler_raises(handlers_mocks, caplog):
    message_handler = handlers_mocks["message_handlers"][0]
    exception_handler = handlers_mocks["exception_handlers"][0]
    event_handler = handlers_mocks["event_handlers"][0]
    message_handler.set_tags.side_effect = Exception("Handler Error")

    tracker = Tracker(
        message_handlers=[message_handler],
        exception_handlers=[exception_handler],
        event_handlers=[event_handler],
    )

    tags = {"key": "value"}

    with caplog.at_level(logging.ERROR):
        tracker.set_tags(tags)

    message_handler.set_tags.assert_called_once_with(tags)
    exception_handler.set_tags.assert_called_once_with(tags)
    event_handler.set_tags.assert_called_once_with(tags)

    log_record = caplog.records[0]
    assert (
        log_record.message
        == f"Error setting tags for handler {message_handler}: Handler Error"
    )


def test_tracker_set_contexts(handlers_mocks):
    message_handler = handlers_mocks["message_handlers"][0]
    exception_handler = handlers_mocks["exception_handlers"][0]
    event_handler = handlers_mocks["event_handlers"][0]

    tracker = Tracker(
        message_handlers=[message_handler],
        exception_handlers=[exception_handler],
        event_handlers=[event_handler],
    )

    contexts = {"context": {"detail": "info"}}
    tracker.set_contexts(contexts)

    message_handler.set_contexts.assert_called_once_with(contexts)
    exception_handler.set_contexts.assert_called_once_with(contexts)
    event_handler.set_contexts.assert_called_once_with(contexts)


def test_tracker_set_contexts_when_handler_raises(handlers_mocks, caplog):
    message_handler = handlers_mocks["message_handlers"][0]
    exception_handler = handlers_mocks["exception_handlers"][0]
    event_handler = handlers_mocks["event_handlers"][0]
    message_handler.set_contexts.side_effect = Exception("Handler Error")

    tracker = Tracker(
        message_handlers=[message_handler],
        exception_handlers=[exception_handler],
        event_handlers=[event_handler],
    )

    contexts = {"context": {"detail": "info"}}

    with caplog.at_level(logging.ERROR):
        tracker.set_contexts(contexts)

    message_handler.set_contexts.assert_called_once_with(contexts)
    exception_handler.set_contexts.assert_called_once_with(contexts)
    event_handler.set_contexts.assert_called_once_with(contexts)

    log_record = caplog.records[0]
    assert (
        log_record.message
        == f"Error setting contexts for handler {message_handler}: Handler Error"
    )
