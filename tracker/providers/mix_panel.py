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
        project_token: str = "YOUR_PROJECT_TOKEN"

    config: MixPanelConfig

    def __init_mix_panel__(self):
        try:
            from mixpanel import Consumer, Mixpanel
        except ImportError as e:
            raise ImportError(
                "mixpanel is required to use MixPanel with Tracker. Please install it via 'pip install mixpanel'."
            ) from e

        self.mp = Mixpanel(
            self.config.project_token,
            consumer=Consumer(retry_limit=2),
        )

    def __init__(self, config: MixPanelConfig) -> None:
        self.config = config
        self.__init_mix_panel__()

    def set_tags(self, tags: Tags):
        logger.info(
            "MixPanel event handler does not provides 'set_tags', ignoring (use 'capture_event()' instead)."
        )

    def set_contexts(self, contexts: Contexts):
        logger.info(
            "MixPanel event handler does not provides 'set_contexts', ignoring (use 'capture_event()' instead)."
        )

    def __extract_distinct_id(self, event: TrackerEvent) -> Optional[str]:
        for key in ["distinct_id", "id", "user_id"]:
            distinct_id = event.tags.get(key, None) if event.tags else None
            if distinct_id:
                return str(distinct_id)
        return None

    def __extract_event_attrs(self, event: TrackerEvent) -> dict:
        ret = {}
        if event.tags:
            ret.update(**event.tags)
        if event.contexts:
            ret.update(**event.contexts)
        for key in ["distinct_id", "id", "user_id"]:
            del ret[key]
        return ret

    def capture_event(self, event: TrackerEvent):
        distinct_id = self.__extract_distinct_id(event=event)
        if not distinct_id:
            return logger.error(
                f"MixPanel attempting to send event without 'distinct_id' tag: {event}"
            )
        event_attrs = self.__extract_event_attrs(event=event)
        self.mp.track(distinct_id, event.event, event_attrs)
