import logging
from dataclasses import dataclass
from typing import Optional

from ..dtos import TrackerEvent
from ..interfaces import ITrackerHandlerEvent
from ..types import Contexts, Tags

logger = logging.getLogger(__name__)


class MixPanelHandlerEvent(ITrackerHandlerEvent):
    @dataclass
    class MixPanelConfig:
        project_token: str
        service_name: str
        retry_limit: int = 2

    config: MixPanelConfig

    _DISTINCT_ID_KEYS = ("distinct_id", "id", "user_id")

    _IMPORT_ERROR_MESSAGE: str = "mixpanel is required to use MixPanel with Tracker. Please install it via 'pip install mixpanel'."
    _SET_TAGS_MESSAGE: str = (
        "MixPanel event handler does not support 'set_tags', ignoring "
        "(pass tags per event via 'capture_event()' instead)."
    )
    _SET_CONTEXTS_MESSAGE: str = (
        "MixPanel event handler does not support 'set_contexts', ignoring "
        "(pass contexts per event via 'capture_event()' instead)."
    )

    def _init_mixpanel(self, config: "MixPanelConfig"):
        try:
            from mixpanel import Consumer, Mixpanel
        except ImportError as e:
            raise ImportError(self._IMPORT_ERROR_MESSAGE) from e  # pragma: no mutate

        self.mp = Mixpanel(  # pragma: no mutate
            config.project_token,
            consumer=Consumer(retry_limit=config.retry_limit),  # pragma: no mutate
        )

    def __init__(self, config: MixPanelConfig) -> None:
        self.config = config
        self.event_source = f"{config.service_name}-server"
        self._init_mixpanel(config)

    def set_tags(self, tags: Tags):
        logger.debug(self._SET_TAGS_MESSAGE)

    def set_contexts(self, contexts: Contexts):
        logger.debug(self._SET_CONTEXTS_MESSAGE)

    def _extract_distinct_id(self, event: TrackerEvent) -> Optional[str]:
        """Busca distinct_id somente nas tags"""
        for key in self._DISTINCT_ID_KEYS:
            distinct_id = event.tags.get(key) if event.tags else None
            if distinct_id:
                return str(distinct_id)
        return None

    def _extract_event_attrs(self, event: TrackerEvent) -> dict:
        ret = {}
        try:
            if event.tags:
                ret.update(event.tags)
            if event.contexts:
                ret.update(event.contexts)
            for key in self._DISTINCT_ID_KEYS:
                ret.pop(key, None)
        except Exception as ex:
            logger.exception(ex)
        finally:
            return ret

    def track(self, distinct_id: str, event: str, event_attrs: dict):
        self.mp.track(distinct_id, event, event_attrs)

    def capture_event(self, event: TrackerEvent):
        distinct_id = self._extract_distinct_id(event=event)
        if not distinct_id:
            distinct_id = self.event_source

        attrs = self._extract_event_attrs(event=event)
        self.track(
            distinct_id=distinct_id,
            event=event.event.value,
            event_attrs={"source": self.event_source, **attrs},
        )
