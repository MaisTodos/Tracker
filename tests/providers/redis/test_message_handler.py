from tracker.providers.redis import RedisMessageHandler


def test_redis_message_handler_capture(redis_core_mock, tracker_message):
    handler = RedisMessageHandler(redis_core_mock)

    handler.set_tags({"t": "v"})
    handler.set_contexts({"ctx": {"k": "v"}})

    handler.capture_message(tracker_message)

    redis_core_mock.set_tags.assert_any_call({"t": "v"})
    redis_core_mock.set_tags.assert_any_call(tracker_message.tags)
    redis_core_mock.set_contexts.assert_any_call({"ctx": {"k": "v"}})
    redis_core_mock.set_contexts.assert_any_call(tracker_message.contexts)
    redis_core_mock.capture_message.assert_called_once_with(
        tracker_message.message.value
    )
