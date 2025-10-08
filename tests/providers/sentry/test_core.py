from unittest.mock import MagicMock

import pytest

from tracker.providers.sentry import SentryCore


def test_sentry_core_init_without_sentry(monkeypatch):
    # Simulate ImportError when sentry_sdk is not installed
    monkeypatch.setitem(__import__("sys").modules, "sentry_sdk", None)

    with pytest.raises(ImportError) as excinfo:
        SentryCore(
            SentryCore.SentryConfig(
                dsn="http://example.com",
                environment="testing",
            ),
        )

    error_message = (
        "sentry-sdk is required to use Sentry with Tracker."
        " Please install it via 'pip install sentry-sdk'."
    )
    assert error_message == str(excinfo.value)


def test_sentry_core_init_without_otel(mock_init):
    before_send_function = lambda event, _: event

    SentryCore(
        SentryCore.SentryConfig(
            dsn="http://example.com",
            environment="testing",
            traces_sample_rate=1.0,
            before_send_function=before_send_function,
            use_otel=False,
        ),
    )

    sentry_logging_integration = mock_init.call_args[1]["integrations"][0]

    mock_init.assert_called_once_with(
        dsn="http://example.com",
        environment="testing",
        integrations=[sentry_logging_integration],
        traces_sample_rate=1.0,
        before_send=before_send_function,
        instrumenter="sentry",
    )


def test_sentry_core_init_with_otel_without_otel_installed(mock_init):
    my_integration = MagicMock()

    SentryCore(
        SentryCore.SentryConfig(
            dsn="http://example.com",
            environment="testing",
            traces_sample_rate=1.0,
            use_otel=True,
            integrations=[my_integration],
        ),
    )

    sentry_logging_integration = mock_init.call_args[1]["integrations"][0]

    mock_init.assert_called_once_with(
        dsn="http://example.com",
        environment="testing",
        integrations=[sentry_logging_integration, my_integration],
        traces_sample_rate=1.0,
        before_send=None,
        instrumenter="sentry",
    )


def test_sentry_core_init_with_otel(mock_init):
    # Mock OpenTelemetry imports
    import sys
    from unittest.mock import MagicMock

    sys.modules["opentelemetry"] = MagicMock()
    sys.modules["opentelemetry.trace"] = MagicMock()
    sys.modules["opentelemetry.propagate"] = MagicMock()
    sys.modules["sentry_sdk.integrations.opentelemetry"] = MagicMock()

    SentryCore(
        SentryCore.SentryConfig(
            dsn="http://example.com",
            environment="testing",
            traces_sample_rate=1.0,
            use_otel=True,
        ),
    )

    # assert OpenTelemetry components were initialized
    from opentelemetry import trace
    from opentelemetry.propagate import set_global_textmap
    from sentry_sdk.integrations.opentelemetry import (
        SentryPropagator,
        SentrySpanProcessor,
    )

    trace.get_tracer_provider().add_span_processor.assert_called_once()
    set_global_textmap.assert_called_once()
    SentrySpanProcessor.assert_called_once()
    SentryPropagator.assert_called_once()

    sentry_logging_integration = mock_init.call_args[1]["integrations"][0]
    mock_init.assert_called_once_with(
        dsn="http://example.com",
        environment="testing",
        integrations=[sentry_logging_integration],
        traces_sample_rate=1.0,
        before_send=None,
        instrumenter="otel",
    )

    # Clean up mocked modules
    del sys.modules["opentelemetry"]
    del sys.modules["opentelemetry.trace"]
    del sys.modules["opentelemetry.propagate"]
    del sys.modules["sentry_sdk.integrations.opentelemetry"]


def test_sentry_core_capture_message(capture_message_mock):
    core = SentryCore(
        SentryCore.SentryConfig(
            dsn="http://example.com",
            environment="testing",
        )
    )

    core.capture_message("Test message")
    capture_message_mock.assert_called_once_with("Test message")


def test_sentry_core_capture_exception(capture_exception_mock):
    core = SentryCore(
        SentryCore.SentryConfig(
            dsn="http://example.com",
            environment="testing",
        )
    )

    exception = Exception("Test exception")

    core.capture_exception(exception)

    capture_exception_mock.assert_called_once_with(exception)


def test_sentry_core_set_tags(set_tag_mock):
    core = SentryCore(
        SentryCore.SentryConfig(
            dsn="http://example.com",
            environment="testing",
        )
    )

    core.set_tags({"key1": "value1", "key2": "value2"})
    core.set_tags({"key3": "value3"})

    set_tag_mock.assert_any_call("key1", "value1")
    set_tag_mock.assert_any_call("key2", "value2")
    set_tag_mock.assert_any_call("key3", "value3")
    assert set_tag_mock.call_count == 3


def test_sentry_core_set_contexts(set_context_mock):
    core = SentryCore(
        SentryCore.SentryConfig(
            dsn="http://example.com",
            environment="testing",
        )
    )

    core.set_contexts(
        {
            "context1": {"field1": "value1", "field2": 2},
            "context2": {"fieldA": True},
        }
    )
    core.set_contexts(
        {
            "context3": {"fieldX": [1, 2, 3]},
        }
    )

    set_context_mock.assert_any_call("context1", {"field1": "value1", "field2": 2})
    set_context_mock.assert_any_call("context2", {"fieldA": True})
    set_context_mock.assert_any_call("context3", {"fieldX": [1, 2, 3]})
    assert set_context_mock.call_count == 3
