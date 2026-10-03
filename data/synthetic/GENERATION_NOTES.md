# Synthetic agent-interaction event generation

`src/seed_events.py` generates the agent-interaction event stream this
platform observes. It is disclosed-synthetic (no real enterprise agent
deployment is available to instrument), but every event's field names
come directly from the real OTel GenAI semantic conventions in
`data/bronze/otel_gen_ai_spans_semconv.yaml` (`gen_ai.request.model`,
`gen_ai.operation.name`, `gen_ai.usage.input_tokens`,
`gen_ai.usage.output_tokens`, `error.type`), not invented field names.

Generation design:

- `RANDOM_SEED = 20261003` for reproducibility.
- Six simulated enterprise "agent workflows" (claims-intake, contract-review,
  support-triage, code-review-assist, expense-audit, knowledge-lookup),
  mirroring the single-agent-pilot-to-multi-agent-operations scaling story
  in the target posting.
- A baseline period (operational, low-latency, low-error) and a
  shifted period (elevated latency and elevated tool-error rate),
  so the drift monitor has a genuine distribution shift to detect, not a
  synthetic step function.
- A small, deliberately placed set of events whose output text contains a
  realistic PII pattern (a phone number formatted with dots instead of
  dashes, e.g. `214.690.1014`) that a naive regex-based redactor is known
  to miss, the trigger for Incident 4.
- Burst load windows (3x normal event rate for a short span) to drive
  Incident 2's Kinesis backpressure condition.
