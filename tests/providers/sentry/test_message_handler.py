from tracker.providers.sentry import SentryMessageHandler


def test_sentry_message_handler_capture(
    sentry_core_mock,
    tracker_message,
):
    message_handler = SentryMessageHandler(sentry_core_mock)

    message_handler.set_tags({"global_tag": "global_value"})
    message_handler.set_contexts({"global_context": {"global_value": 123}})

    message_handler.capture_message(tracker_message)

    sentry_core_mock.set_tags.assert_called_once_with({"global_tag": "global_value"})
    sentry_core_mock.set_contexts.assert_called_once_with(
        {"global_context": {"global_value": 123}}
    )
    sentry_core_mock.capture_message.assert_called_once_with(
        tracker_message.message.value
    )


def test_sentry_message_handler_capture_with_tags_and_contexts(
    sentry_core_mock,
    tracker_message,
):
    message_handler = SentryMessageHandler(sentry_core_mock)

    message_handler.set_tags({"global_tag": "global_value"})
    message_handler.set_contexts({"global_context": {"global_value": 123}})

    tracker_message.tags = {"tag1": "value1"}
    tracker_message.contexts = {"context1": {"key": "value"}}

    message_handler.capture_message(tracker_message)

    sentry_core_mock.set_tags.assert_any_call({"global_tag": "global_value"})
    sentry_core_mock.set_tags.assert_any_call(tracker_message.tags)
    assert sentry_core_mock.set_tags.call_count == 2

    sentry_core_mock.set_contexts.assert_any_call(
        {"global_context": {"global_value": 123}}
    )
    sentry_core_mock.set_contexts.assert_any_call(tracker_message.contexts)
    assert sentry_core_mock.set_contexts.call_count == 2

    sentry_core_mock.capture_message.assert_called_once_with(
        tracker_message.message.value
    )
