import logging

from tracker.providers.logger import LoggerCore


def test_logger_core_init_with_config():
    logger = logging.getLogger("Tracker.LoggerCore")
    logger.handlers = []

    stream_handler = logging.StreamHandler()
    LoggerCore(LoggerCore.LoggerConfig(logger_handler=stream_handler))

    logger = logging.getLogger("Tracker.LoggerCore")
    assert len(logger.handlers) == 1
    assert logger.handlers[0] == stream_handler

    LoggerCore(LoggerCore.LoggerConfig())

    # No new handler added
    logger = logging.getLogger("Tracker.LoggerCore")
    assert len(logger.handlers) == 1
    assert logger.handlers[0] == stream_handler


def test_logger_core_init_without_config():
    logger = logging.getLogger("Tracker.LoggerCore")
    logger.handlers = []

    LoggerCore(LoggerCore.LoggerConfig())

    logger = logging.getLogger("Tracker.LoggerCore")
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)


def test_logger_core_set_tags_logs_debug(logger_core, caplog):
    with caplog.at_level(logging.DEBUG, logger="Tracker.LoggerCore"):
        logger_core.set_tags({"tag1": "value1"})

    assert LoggerCore._SET_TAGS_MESSAGE in [r.message for r in caplog.records]


def test_logger_core_set_contexts_logs_debug(logger_core, caplog):
    with caplog.at_level(logging.DEBUG, logger="Tracker.LoggerCore"):
        logger_core.set_contexts({"context1": "value1"})

    assert LoggerCore._SET_CONTEXTS_MESSAGE in [r.message for r in caplog.records]
