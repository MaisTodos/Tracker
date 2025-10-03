import logging
from huble import setup_core
from core import set_current_trace_id, reset_current_trace_id

def test_setup_core_instala_filter(mem_logger):
    setup_core()
    tok = set_current_trace_id("4a750618-2ad1-494f-9142-bbe0a6e55874")
    try:
        logging.warning("oi")
    finally:
        reset_current_trace_id(tok)
    rec = mem_logger.records[0]
    assert getattr(rec, "huble_trace_id") == "4a750618-2ad1-494f-9142-bbe0a6e55874"
