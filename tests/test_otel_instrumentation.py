from src.seed_events import generate_events
from src.otel_instrumentation import emit_spans


def test_real_otel_spans_carry_gen_ai_semconv_attributes():
    baseline, _, _ = generate_events()
    spans = emit_spans(baseline[:20])
    assert len(spans) == 20
    for sp in spans:
        attrs = dict(sp.attributes)
        assert "gen_ai.operation.name" in attrs
        assert "gen_ai.request.model" in attrs
        assert "gen_ai.usage.input_tokens" in attrs
        assert "gen_ai.usage.output_tokens" in attrs


def test_error_spans_set_error_status():
    baseline, shifted, _ = generate_events()
    error_events = [e for e in shifted if e["error.type"]]
    assert error_events, "expected at least one real error event in the shifted period"
    spans = emit_spans(error_events[:5])
    for sp in spans:
        assert sp.status.status_code.name == "ERROR"
