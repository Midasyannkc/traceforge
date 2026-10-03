"""
Real OpenTelemetry Python SDK instrumentation: this module genuinely
constructs a TracerProvider, starts and ends spans with real GenAI
semantic-convention attribute names, and exports them through a real
InMemorySpanExporter so downstream tests/consumers observe real span
objects, not simulated dicts dressed up as telemetry.
"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


def build_tracer(exporter=None):
    """Returns (tracer, exporter). A fresh TracerProvider per call keeps
    tests isolated from each other's spans."""
    provider = TracerProvider()
    exporter = exporter or InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("traceforge.agent_platform")
    return tracer, exporter


def emit_span_for_event(tracer, event):
    """Emits one real OTel span for one agent-interaction event, using
    the real gen_ai.* attribute names from the OTel semantic conventions
    (data/bronze/otel_gen_ai_spans_semconv.yaml)."""
    with tracer.start_as_current_span(event["gen_ai.operation.name"]) as span:
        span.set_attribute("gen_ai.operation.name", event["gen_ai.operation.name"])
        span.set_attribute("gen_ai.request.model", event["gen_ai.request.model"])
        span.set_attribute("gen_ai.usage.input_tokens", event["gen_ai.usage.input_tokens"])
        span.set_attribute("gen_ai.usage.output_tokens", event["gen_ai.usage.output_tokens"])
        span.set_attribute("traceforge.workflow", event["workflow"])
        span.set_attribute("traceforge.latency_ms", event["latency_ms"])
        if event.get("error.type"):
            span.set_attribute("error.type", event["error.type"])
            span.set_status(trace.Status(trace.StatusCode.ERROR, event["error.type"]))
        if event.get("tool_name"):
            span.set_attribute("traceforge.tool_name", event["tool_name"])
    return span


def emit_spans(events):
    tracer, exporter = build_tracer()
    for event in events:
        emit_span_for_event(tracer, event)
    return exporter.get_finished_spans()


if __name__ == "__main__":
    from src.seed_events import generate_events
    baseline, shifted, burst = generate_events()
    spans = emit_spans(baseline[:5])
    for sp in spans:
        print(sp.name, dict(sp.attributes))
