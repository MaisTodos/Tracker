import logging
import uuid
from ..core import get_current_trace_id, set_current_trace_id

class HubleTraceFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        tid = get_current_trace_id()
        if not tid:
            tid = str(uuid.uuid4())
            set_current_trace_id(tid)
        setattr(record, "trace_id", tid)
        return True
