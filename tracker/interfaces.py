from abc import ABC, abstractmethod

from .dtos import TrackerEvent, TrackerException, TrackerMessage
from .types import Contexts, Tags


class ISetMixin(ABC):
    @abstractmethod
    def set_tags(self, tags: Tags):  # pragma: no cover
        ...

    @abstractmethod
    def set_contexts(self, contexts: Contexts):  # pragma: no cover
        ...


class ITrackerHandlerException(ISetMixin, ABC):
    @abstractmethod
    def capture_exception(self, tracker_exception: TrackerException):  # pragma: no cover
        ...


class ITrackerHandlerMessage(ISetMixin, ABC):
    @abstractmethod
    def capture_message(self, tracker_message: TrackerMessage):  # pragma: no cover
        ...


class ITrackerHandlerEvent(ISetMixin, ABC):
    @abstractmethod
    def capture_event(self, tracker_event: TrackerEvent):  # pragma: no cover
        ...
