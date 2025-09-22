from tracker.providers.redis import RedisExceptionHandler


def test_redis_exception_handler_capture(redis_core_mock, tracker_exception):
    handler = RedisExceptionHandler(redis_core_mock)

    handler.set_tags({"t": "v"})
    handler.set_contexts({"ctx": {"k": "v"}})

    handler.capture_exception(tracker_exception)

    redis_core_mock.set_tags.assert_any_call({"t": "v"})
    redis_core_mock.set_tags.assert_any_call(tracker_exception.tags)
    redis_core_mock.set_contexts.assert_any_call({"ctx": {"k": "v"}})
    redis_core_mock.set_contexts.assert_any_call(tracker_exception.contexts)
    redis_core_mock.capture_exception.assert_called_once_with(
        tracker_exception.exception
    )
