"""
Generate the disclosed-synthetic agent-interaction event stream this
platform observes, using real OTel GenAI semantic-convention field names
(see data/bronze/SOURCE.md and data/synthetic/GENERATION_NOTES.md).
"""
import random
from datetime import datetime, timedelta, timezone

RANDOM_SEED = 20261003

WORKFLOWS = [
    "claims-intake",
    "contract-review",
    "support-triage",
    "code-review-assist",
    "expense-audit",
    "knowledge-lookup",
]

MODELS = ["anthropic.claude-3-5-sonnet", "anthropic.claude-3-haiku", "meta.llama3-70b"]

TOOLS = ["kb_lookup", "ticket_update", "policy_lookup", "code_search", "expense_db_query"]

# a realistic phone-number-shaped PII pattern that a naive dash/space-only
# regex redactor will miss (dot-separated), the trigger for Incident 4
DOTTED_PHONE_PII = "214.690.1014"


def _span(ts, workflow, model, operation, latency_ms, input_tokens, output_tokens,
          error_type=None, output_text=None, tool_name=None):
    return {
        "timestamp": ts.isoformat(),
        "workflow": workflow,
        "gen_ai.operation.name": operation,
        "gen_ai.request.model": model,
        "gen_ai.usage.input_tokens": input_tokens,
        "gen_ai.usage.output_tokens": output_tokens,
        "latency_ms": latency_ms,
        "error.type": error_type,
        "tool_name": tool_name,
        "output_text": output_text,
        "event_id": f"{workflow}-{ts.strftime('%Y%m%dT%H%M%S%f')}",
    }


def generate_events(n_baseline=600, n_shifted=200, n_burst=150):
    """
    Returns (baseline_events, shifted_events, burst_events).

    baseline: normal operating period, low latency, low error rate.
    shifted: a real distribution shift -- elevated latency and elevated
      tool-error rate -- for the drift-monitor incident.
    burst: a short high-rate window for the Kinesis backpressure incident.
    """
    rng = random.Random(RANDOM_SEED)
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)

    baseline = []
    t = start
    for i in range(n_baseline):
        t += timedelta(seconds=rng.randint(5, 30))
        workflow = rng.choice(WORKFLOWS)
        model = rng.choice(MODELS)
        latency = max(80, int(rng.gauss(420, 60)))
        error = "ToolTimeoutError" if rng.random() < 0.02 else None
        output_text = "Request handled." if rng.random() > 0.01 else (
            f"Please call the requester back at {DOTTED_PHONE_PII} to confirm."
        )
        baseline.append(_span(
            t, workflow, model, "chat", latency,
            input_tokens=rng.randint(200, 900), output_tokens=rng.randint(40, 300),
            error_type=error, output_text=output_text,
            tool_name=rng.choice(TOOLS) if rng.random() < 0.4 else None,
        ))

    shift_start = t + timedelta(hours=6)
    shifted = []
    t = shift_start
    for i in range(n_shifted):
        t += timedelta(seconds=rng.randint(5, 30))
        workflow = rng.choice(WORKFLOWS)
        model = rng.choice(MODELS)
        # real, deliberate shift: latency up ~2.4x, tool error rate up ~9x
        latency = max(150, int(rng.gauss(1010, 140)))
        error = "ToolTimeoutError" if rng.random() < 0.18 else None
        output_text = "Request handled." if rng.random() > 0.03 else (
            f"You can reach us at {DOTTED_PHONE_PII} for follow-up."
        )
        shifted.append(_span(
            t, workflow, model, "chat", latency,
            input_tokens=rng.randint(200, 900), output_tokens=rng.randint(40, 300),
            error_type=error, output_text=output_text,
            tool_name=rng.choice(TOOLS) if rng.random() < 0.4 else None,
        ))

    burst_start = t + timedelta(minutes=30)
    burst = []
    t = burst_start
    for i in range(n_burst):
        t += timedelta(milliseconds=rng.randint(200, 900))  # ~3x normal rate
        workflow = rng.choice(WORKFLOWS)
        model = rng.choice(MODELS)
        latency = max(80, int(rng.gauss(420, 60)))
        burst.append(_span(
            t, workflow, model, "chat", latency,
            input_tokens=rng.randint(200, 900), output_tokens=rng.randint(40, 300),
            error_type=None, output_text="Request handled.",
            tool_name=rng.choice(TOOLS) if rng.random() < 0.4 else None,
        ))

    return baseline, shifted, burst


if __name__ == "__main__":
    b, s, burst = generate_events()
    print(f"baseline={len(b)} shifted={len(s)} burst={len(burst)}")
