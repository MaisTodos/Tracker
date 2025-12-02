import logging
from dataclasses import dataclass
from typing import Optional
from uuid import NAMESPACE_DNS, UUID, uuid5

from ..dtos import TrackerEvent
from ..interfaces import ITrackerHandlerEvent
from ..types import Contexts, Tags

logger = logging.getLogger(__name__)


class MixPanelHandlerEvent(ITrackerHandlerEvent):
    @dataclass
    class MixPanelConfig:
        project_token: str = "YOUR_PROJECT_TOKEN"
        distinct_id_salt: str = "DISTRIBUTED_SALT"
        distinct_id_namespace: UUID = NAMESPACE_DNS
        retry_limit: int = 2

    config: MixPanelConfig

    _IMPORT_ERROR_MESSAGE: str = "mixpanel is required to use MixPanel with Tracker. Please install it via 'pip install mixpanel'."
    _SET_TAGS_MESSAGE: str = "MixPanel event handler does not provides 'set_tags', ignoring (use 'capture_event()' instead)."
    _SET_CONTEXT_MESSAGE: str = "MixPanel event handler does not provides 'set_contexts', ignoring (use 'capture_event()' instead)."
    _NO_DISTINCT_ID_MESSAGE: str = (
        "MixPanel attempting to send event without 'distinct_id' tag: {}"
    )

    def __init_mix_panel__(self):
        try:
            from mixpanel import Consumer, Mixpanel
        except ImportError as e:
            raise ImportError(self._IMPORT_ERROR_MESSAGE) from e  # pragma: no mutate

        self.mp = Mixpanel(  # pragma: no mutate
            self.config.project_token,
            consumer=Consumer(retry_limit=self.config.retry_limit),  # pragma: no mutate
        )

    def __init__(self, config: MixPanelConfig) -> None:
        self.config = config
        self.__init_mix_panel__()

    def set_tags(self, tags: Tags):
        logger.info(self._SET_TAGS_MESSAGE)

    def set_contexts(self, contexts: Contexts):
        logger.info(self._SET_CONTEXT_MESSAGE)

    def _extract_distinct_id(self, event: TrackerEvent) -> Optional[str]:
        for key in ["distinct_id", "id", "user_id"]:
            distinct_id = event.tags.get(key) if event.tags else None
            if distinct_id:
                return str(distinct_id)
        return None

    def _extract_event_attrs(self, event: TrackerEvent) -> dict:
        ret = {}
        try:
            if event.tags:
                ret.update(**event.tags)
            if event.contexts:
                ret.update(**event.contexts)
            for key in ["distinct_id", "id", "user_id"]:
                del ret[key]
        except Exception as ex:
            logger.exception(ex)
        finally:
            return ret

    def track(self, distinct_id: str, event: str, event_attrs: dict):
        self.mp.track(distinct_id, event, event_attrs)

    def generate_distinct_id(self, key: str) -> str:
        return str(
            uuid5(
                namespace=self.config.distinct_id_namespace,
                name=f"{key}{self.config.distinct_id_salt}",
            )
        )

    def capture_event(self, event: TrackerEvent):
        distinct_id = self._extract_distinct_id(event=event)
        if not distinct_id:
            return logger.error(self._NO_DISTINCT_ID_MESSAGE.format(event))
        attrs = self._extract_event_attrs(event=event)
        self.track(distinct_id=distinct_id, event=event.event.value, event_attrs=attrs)
