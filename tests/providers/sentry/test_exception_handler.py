from tracker.providers.sentry import SentryExceptionHandler


def test_sentry_exception_handler_capture(
    sentry_core_mock,
    tracker_exception,
):
    exception_handler = SentryExceptionHandler(sentry_core_mock)

    exception_handler.set_tags({"global_tag": "global_value"})
    exception_handler.set_contexts({"global_context": {"global_value": 123}})

    exception_handler.capture_exception(tracker_exception)

    sentry_core_mock.set_tags.assert_called_once_with({"global_tag": "global_value"})
    sentry_core_mock.set_contexts.assert_called_once_with(
        {"global_context": {"global_value": 123}}
    )
    sentry_core_mock.capture_exception.assert_called_once_with(
        tracker_exception.exception
    )


def test_sentry_exception_handler_capture_with_tags_and_contexts(
    sentry_core_mock,
    tracker_exception,
):
    exception_handler = SentryExceptionHandler(sentry_core_mock)

    exception_handler.set_tags({"global_tag": "global_value"})
    exception_handler.set_contexts({"global_context": {"global_value": 123}})

    tracker_exception.tags = {"tag1": "value1"}
    tracker_exception.contexts = {"context1": {"key": "value"}}

    exception_handler.capture_exception(tracker_exception)

    sentry_core_mock.set_tags.assert_any_call({"global_tag": "global_value"})
    sentry_core_mock.set_tags.assert_any_call(tracker_exception.tags)
    assert sentry_core_mock.set_tags.call_count == 2

    sentry_core_mock.set_contexts.assert_any_call(
        {"global_context": {"global_value": 123}}
    )
    sentry_core_mock.set_contexts.assert_any_call(tracker_exception.contexts)
    assert sentry_core_mock.set_contexts.call_count == 2

    sentry_core_mock.capture_exception.assert_called_once_with(
        tracker_exception.exception
    )
