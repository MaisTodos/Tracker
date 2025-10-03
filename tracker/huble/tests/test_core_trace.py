from core import (
    CANON_TRACE_HEADER,
    get_current_trace_id, set_current_trace_id, reset_current_trace_id,
    get_trace_id_if_any, get_or_create_trace_id,
)

def test_context_var_roundtrip():
    assert get_current_trace_id() is None
    tok = set_current_trace_id("11111111-1111-1111-1111-111111111111")
    try:
        assert get_current_trace_id() == "11111111-1111-1111-1111-111111111111"
    finally:
        reset_current_trace_id(tok)
    assert get_current_trace_id() is None

def test_get_trace_id_if_any_present_case_insensitive():
    headers = {CANON_TRACE_HEADER.lower(): "4a750618-2ad1-494f-9142-bbe0a6e55874"}
    assert get_trace_id_if_any(headers) == "4a750618-2ad1-494f-9142-bbe0a6e55874"

def test_get_or_create_trace_id_generated_when_missing():
    tid, source = get_or_create_trace_id({})
    assert source == "generated"
    assert len(tid) == 36 and tid.count("-") == 4
