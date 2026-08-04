import logging
from enum import Enum
from unittest.mock import MagicMock, patch

import pytest

from tracker.dtos import TrackerEvent
from tracker.providers.mix_panel import MixPanelHandlerEvent


class EventEnum(str, Enum):
    FOO = "bar"


def make_config(**overrides) -> MixPanelHandlerEvent.MixPanelConfig:
    config = {
        "project_token": "foobar",
        "service_name": "svc",
        "secret": "a" * 32,
    }
    config.update(overrides)
    return MixPanelHandlerEvent.MixPanelConfig(**config)


def make_handler(**overrides) -> MixPanelHandlerEvent:
    return MixPanelHandlerEvent(config=make_config(**overrides))


def test_mix_panel_handler_init_without_mixpanel(monkeypatch):
    # Simulate ImportError when mixpanel is not installed
    monkeypatch.setitem(__import__("sys").modules, "mixpanel", None)

    with pytest.raises(ImportError) as excinfo:
        make_handler()

    assert MixPanelHandlerEvent._IMPORT_ERROR_MESSAGE == str(excinfo.value)


def test_mix_panel_handler_init_stores_config():
    config = make_config()
    handler = MixPanelHandlerEvent(config=config)
    assert handler.config is config
    assert handler.event_source == "svc-server"


def test_mix_panel_handler_init_invalid_secret_length():
    with pytest.raises(ValueError) as err:
        make_handler(secret="a" * 16)

    assert (
        err.value.args[0]
        == "Error in secret length. Must be at least 32 characters long."
    )


def test_mix_panel_handler__extract_distinct_id():
    handler = make_handler()
    for key in ["distinct_id", "id", "user_id"]:
        assert (
            handler._extract_distinct_id(
                event=TrackerEvent(event=EventEnum.FOO, tags={key: "a"})
            )
            == "a"
        )
    assert (
        handler._extract_distinct_id(
            event=TrackerEvent(event=EventEnum.FOO, tags={"foo": "bar"})
        )
        is None
    )


def test_mix_panel_handler__extract_event_attrs():
    handler = make_handler()
    result = handler._extract_event_attrs(
        event=TrackerEvent(
            event=EventEnum.FOO,
            tags={
                "distinct_id": "a",
                "id": "a",
                "user_id": "a",
                "key1": "value1",
            },
            contexts={"context": {"key2": "value2"}},
        )
    )
    assert result == {"key1": "value1", "context": {"key2": "value2"}}


def test_mix_panel_handler__extract_event_attrs_contexts_only():
    handler = make_handler()
    result = handler._extract_event_attrs(
        event=TrackerEvent(
            event=EventEnum.FOO, contexts={"context": {"key2": "value2"}}
        )
    )
    assert result == {"context": {"key2": "value2"}}


def test_mix_panel_handler__extract_event_attrs_no_id_leak():
    # bug 1: events with only some id keys must not raise/log nor leak id keys
    handler = make_handler()
    with patch("tracker.providers.mix_panel.logger") as mock_logger:
        result = handler._extract_event_attrs(
            event=TrackerEvent(
                event=EventEnum.FOO, tags={"distinct_id": "a", "foo": "bar"}
            )
        )
    assert result == {"foo": "bar"}
    mock_logger.exception.assert_not_called()


def test_mix_panel_handler__extract_event_attrs_exception():
    handler = make_handler()
    with patch("tracker.providers.mix_panel.logger") as mock_logger:
        mock_logger.exception = MagicMock()
        mock_event = MagicMock()
        mock_event.tags = 13
        handler._extract_event_attrs(event=mock_event)
        assert isinstance(mock_logger.exception.call_args[0][0], Exception)


def test_mix_panel_handler_set_tags_and_contexts_log_debug(caplog):
    handler = make_handler()
    with caplog.at_level(logging.DEBUG, logger="tracker.providers.mix_panel"):
        handler.set_tags({"global_tag": "g"})
        handler.set_contexts({"global_ctx": {"k": "v"}})

    messages = [record.message for record in caplog.records]
    assert handler._SET_TAGS_MESSAGE in messages
    assert handler._SET_CONTEXTS_MESSAGE in messages


def test_hash_distinct_id_different_values():
    handler = make_handler()

    first = handler.hash_distinct_id(value="12345678901")
    second = handler.hash_distinct_id(value="98765432100")

    assert first != second


def test_hash_distinct_id_different_secrets():
    document = "12345678901"

    first_handler = make_handler(secret="a" * 32)
    first = first_handler.hash_distinct_id(value=document)

    second_handler = make_handler(secret="b" * 32)
    second = second_handler.hash_distinct_id(value=document)

    assert first != second


def test_hash_distinct_id_is_deterministic():
    handler = make_handler()

    document = "12345678901"
    document_with_mask = "123.456.789-01"

    first = handler.hash_distinct_id(value=document)
    second = handler.hash_distinct_id(value=document)
    with_mask = handler.hash_distinct_id(value=document_with_mask)

    assert first == second == with_mask


def test_mix_panel_handler_track():
    handler = make_handler()
    handler.mp.track = MagicMock()

    handler.track(distinct_id="d", event="e", event_attrs={"a": 1})

    handler.mp.track.assert_called_once_with("d", "e", {"a": 1})


def test_mix_panel_handler_capture_event():
    handler = make_handler(service_name="svc")
    handler.mp.track = MagicMock()

    handler.capture_event(
        event=TrackerEvent(
            event=EventEnum.FOO, tags={"distinct_id": "distinct_id", "foo": "bar"}
        )
    )
    handler.mp.track.assert_called_once_with(
        "distinct_id", "bar", {"source": "svc-server", "foo": "bar"}
    )


def test_mix_panel_handler_capture_event_without_distinct_id():
    # bug 6: no distinct_id falls back to the raw "{service_name}-server" event source
    handler = make_handler(service_name="svc")
    handler.mp.track = MagicMock()

    handler.capture_event(event=TrackerEvent(event=EventEnum.FOO, tags={"foo": "bar"}))

    handler.mp.track.assert_called_once_with(
        "svc-server", "bar", {"source": "svc-server", "foo": "bar"}
    )
