import pytest

from tracker.providers.logger import LoggerCore


@pytest.fixture()
def logger_core():
    return LoggerCore(LoggerCore.LoggerConfig())
