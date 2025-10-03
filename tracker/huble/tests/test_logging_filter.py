import logging
from logging.filter import HubleTraceFilter
from core import set_current_trace_id, reset_current_trace_id

def test_filter_injeta_trace_id(mem_logger):
    root = logging.getLogger()
    f = HubleTraceFilter()
    root.addFilter(f)
    tok = set_current_trace_id("4a750618-2ad1-494f-9142-bbe0a6e55874")
    try:
        logging.info("hello")
    finally:
        reset_current_trace_id(tok)
        root.removeFilter(f)

    assert len(mem_logger.records) == 1
    rec = mem_logger.records[0]
    assert getattr(rec, "huble_trace_id") == "4a750618-2ad1-494f-9142-bbe0a6e55874"
