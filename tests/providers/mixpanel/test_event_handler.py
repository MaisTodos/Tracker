from enum import Enum
from unittest.mock import ANY, MagicMock, patch

import pytest

from tracker.dtos import TrackerEvent
from tracker.providers.mix_panel import MixPanelHandlerEvent


class EventEnum(str, Enum):
    FOO = "bar"


def test_sentry_core_init_without_sentry(monkeypatch):
    # Simulate ImportError when mixpanel is not installed
    monkeypatch.setitem(__import__("sys").modules, "mixpanel", None)

    with pytest.raises(ImportError) as excinfo:
        MixPanelHandlerEvent(
            config=MixPanelHandlerEvent.MixPanelConfig(project_token="foobar")
        )

    assert MixPanelHandlerEvent._IMPORT_ERROR_MESSAGE == str(excinfo.value)


@patch("tracker.providers.mix_panel.uuid5")
def test_mix_panel_handler_generate_distinct_id(mock_uuid5):
    handler = MixPanelHandlerEvent(
        config=MixPanelHandlerEvent.MixPanelConfig(project_token="foobar")
    )
    distinct = handler.generate_distinct_id(key="foobar")
    assert isinstance(distinct, str)
    mock_uuid5.assert_called_once_with(
        namespace=handler.config.distinct_id_namespace,
        name=f"foobar{handler.config.distinct_id_salt}",
    )


def test_mix_panel_handler__extract_event_attrs():
    handler = MixPanelHandlerEvent(
        config=MixPanelHandlerEvent.MixPanelConfig(project_token="foobar")
    )
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


def test_mix_panel_handler__extract_event_attrs_exception():
    handler = MixPanelHandlerEvent(
        config=MixPanelHandlerEvent.MixPanelConfig(project_token="foobar")
    )
    with patch("tracker.providers.mix_panel.logger") as mock_logger:
        mock_logger.exception = MagicMock()
        mock_event = MagicMock()
        mock_event.tags = 13
        handler._extract_event_attrs(event=mock_event)
        assert isinstance(mock_logger.exception.call_args[0][0], Exception)


def test_mix_panel_handler__extract_distinct_id():
    handler = MixPanelHandlerEvent(
        config=MixPanelHandlerEvent.MixPanelConfig(project_token="foobar")
    )
    for key in ["distinct_id", "id", "user_id"]:
        assert (
            handler._extract_distinct_id(
                event=TrackerEvent(
                    event=EventEnum.FOO,
                    tags={
                        key: "a",
                    },
                )
            )
            == "a"
        )
    assert (
        handler._extract_distinct_id(
            event=TrackerEvent(
                event=EventEnum.FOO,
                tags={
                    "foo": "bar",
                },
            )
        )
        == None
    )


def test_mix_panel_handler_capture_event_without_distinct_id():
    handler = MixPanelHandlerEvent(
        config=MixPanelHandlerEvent.MixPanelConfig(project_token="foobar")
    )
    handler.mp.track = MagicMock()

    mock_event = MagicMock()

    mock_event.tags = {"distinct_id": None}
    with patch("tracker.providers.mix_panel.logger") as mock_logger:
        mock_logger.error = MagicMock()
        handler.capture_event(event=mock_event)
        mock_logger.error.assert_called_with(
            handler._NO_DISTINCT_ID_MESSAGE.format(mock_event)
        )
    handler.mp.track.assert_not_called()


def test_mix_panel_handler_capture_event():
    handler = MixPanelHandlerEvent(
        config=MixPanelHandlerEvent.MixPanelConfig(project_token="foobar")
    )
    handler.mp.track = MagicMock()

    mock_event = MagicMock()
    mock_event.event.value = "event_name"

    mock_event.tags = {
        "distinct_id": "distinct_id",
        "foo": "bar",
    }
    handler.capture_event(event=mock_event)
    handler.mp.track.assert_called_once_with(
        "distinct_id", mock_event.event.value, {"foo": "bar"}
    )


def test_mix_panel_handler_logs():
    handler = MixPanelHandlerEvent(
        config=MixPanelHandlerEvent.MixPanelConfig(project_token="foobar")
    )

    with patch("tracker.providers.mix_panel.logger") as mock_logger:
        mock_logger.info = MagicMock()
        handler.set_tags(tags=MagicMock())
        mock_logger.info.assert_called_with(handler._SET_TAGS_MESSAGE)
        handler.set_contexts(contexts=MagicMock())
        mock_logger.info.assert_called_with(handler._SET_CONTEXT_MESSAGE)
        mock_logger.info.assert_called_with(handler._SET_CONTEXT_MESSAGE)
