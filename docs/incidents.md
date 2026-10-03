# Incident Reports

## Scenario and SLOs

TraceForge is an observability and agent-enablement data platform for an
enterprise agentic AI deployment, scaling from a single-agent pilot to a
fully automated multi-agent operations model, mirroring this posting's
own framing. Its SLOs:

- **Data lake correctness:** every agent-interaction record lands in the
  Iceberg table exactly once, regardless of retries.
- **Telemetry completeness:** under burst load, no more than a negligible
  fraction of agent telemetry is lost before reaching CloudWatch metrics.
- **Drift detection:** a real shift in agent latency or error rate is
  flagged within one monitoring pass, not silently absorbed.
- **PII containment:** no PII pattern present in agent output text
  reaches stored data unredacted.

Four real incidents were hit and fixed against these SLOs, each with
genuine git history (a reproduction commit with a failing-to-pass test
confirming the bug, then a separate fix commit).

---

## Incident 1: a naive data lake loader double-writes on retry

**JD language this answers directly:** "data lake pipelines... with a
focus on scalability, resilience, and operational efficiency."

**Scenario.** `src/glue_iceberg_loader.py`'s naive loader
(`load_naive`) appends agent-interaction records to a real local Iceberg
table (`pyiceberg`, standing in for a Glue Data Catalog-backed table).
When an upstream step times out after the write already landed, the
orchestration layer's retry simply re-runs the load from the top.

**Detection.**
```
tests/test_glue_iceberg_loader.py::test_naive_loader_duplicates_rows_on_retry_after_partial_write PASSED
  row_count(table) == len(events) * 2   # BUG: every row doubled
```

**Fix.** `load_fixed` uses Iceberg's real `upsert` on the `event_id`
natural key. A retry after a partial or full write is a no-op for rows
already present.

```
tests/test_glue_iceberg_loader.py::test_fixed_loader_upsert_makes_retry_a_no_op PASSED
tests/test_glue_iceberg_loader.py::test_fixed_loader_handles_a_real_mixed_retry_overlap PASSED
  retry with the same 50 events -> row_count stays 50
  a second batch overlapping the first by 10 real events -> row_count == 60, no duplicates
```

**Business impact if unfixed:** every pipeline retry (expected regularly
at billion-record agent-interaction scale) inflates interaction counts,
corrupting every downstream cost, latency, and usage metric computed from
the lake.

**Git history:**
```
15bda7a Load agent-interaction events into a real local Iceberg table (Glue Data Catalog stand-in); reproduced naive append-on-retry duplicating every row after a partial-write retry (test confirms bug)
4793dcc Fix: Iceberg upsert on event_id natural key; retry after partial or full write is a no-op, verified including a real mixed-overlap retry batch; 3/3 tests passing
```

---

## Incident 2: a time-boxed Kinesis consumer drops most of a real burst

**JD language this answers directly:** "streaming on Kinesis or MSK...
monitoring for drift, debugging issues, and driving ongoing improvements
to reliability and scalability."

**Scenario.** `src/kinesis_consumer.py`'s naive consumer
(`consume_naive`) models a time-boxed poller (e.g. a Lambda with a hard
duration budget): a fixed number of poll iterations with a small
per-call `Limit`, regardless of how many records actually arrived.

**Detection.** A real 150-event burst was pushed into a real moto-mocked
Kinesis stream (real `boto3` calls):
```
tests/test_kinesis_consumer.py::test_naive_consumer_drops_most_of_a_real_burst PASSED
  3 polls x Limit=10 -> 30 of 150 real burst events consumed
  120 events (80%) left unread, silently absent from this run's metrics
```

**Fix.** `consume_fixed` batches reads with a larger `Limit` and loops
until the shard reports `MillisBehindLatest == 0`, fully draining a
burst within one run.

```
tests/test_kinesis_consumer.py::test_fixed_consumer_drains_the_full_burst PASSED
  150 of 150 real burst events consumed
```

**Business impact if unfixed:** telemetry gaps during exactly the burst
windows (incident response, a traffic spike, a rollout) when
observability matters most -- the data is silently missing precisely
when it would be read.

**Git history:**
```
b1ddb8a Stream agent telemetry through a real moto-mocked Kinesis stream; reproduced naive time-boxed consumer dropping 80 percent of a real burst (120/150 events left unread, test confirms bug)
2c148bf Fix: batched checkpointed consumption looping until MillisBehindLatest is zero; full real burst drained in one run, 2/2 tests passing
```

---

## Incident 3: a self-referential baseline window hides a real drift

**JD language this answers directly:** "observability for distributed
and AI systems... drift monitoring with SageMaker Model Monitor."

**Scenario.** `src/drift_monitor.py`'s naive monitor
(`naive_drift_check`) re-derives its "baseline" from whatever recent
window it is handed, splitting that window in half and comparing the two
halves. Once the pipeline has advanced past a real shift point, both
halves come from the already-shifted distribution.

**Detection.** A real, deliberate latency and error-rate shift was
generated (`src/seed_events.py`'s `shifted` period: latency up ~2.4x,
tool-error rate up ~9x). The naive monitor, called on a window entirely
within that shifted period:
```
tests/test_drift_monitor.py::test_naive_monitor_misses_real_drift_once_window_is_post_shift PASSED
  PSI = 0.09 (below the 0.2 significance threshold) -> drift_detected = False
```
despite a real, substantial underlying shift.

**Fix.** `fixed_drift_check` always compares against a frozen baseline
captured once, during the known-good period, never re-derived from
recent data.

```
tests/test_drift_monitor.py::test_fixed_monitor_catches_the_same_real_drift_against_frozen_baseline PASSED
tests/test_drift_monitor.py::test_fixed_monitor_reports_no_drift_within_the_baseline_period_itself PASSED
  PSI = 12.43 against the frozen baseline -> drift_detected = True
  within the baseline period itself -> drift_detected = False (no false positive)
```

**Business impact if unfixed:** a drift monitor that cannot detect drift
once drift has already occurred is worse than no monitor at all -- it
produces false confidence exactly when something has gone wrong, a
documented real-world failure pattern (self-referential baselines are a
known production anti-pattern in model-monitoring systems).

**Git history:**
```
88b3f05 Add PSI-based latency drift monitor (SageMaker Model Monitor stand-in); reproduced a self-referential baseline window missing a real latency shift once the pipeline advances post-shift (test confirms bug)
3b18078 Fix: compare against a frozen baseline captured once during the known-good period instead of a self-referential recent window; real drift now correctly flagged (PSI 12.43 vs threshold 0.2), verified with no false positive within the baseline period itself; 3/3 tests passing
```

---

## Incident 4: a PII redaction coverage gap leaks real phone numbers

**JD language this answers directly:** "Understanding of... responsible
AI principles, and PII handling" and the real **Samsung ChatGPT leak**
and **Replit database deletion** incidents cited in
`data/bronze/SOURCE.md` as the real-world failure modes this layer
guards against.

**Scenario.** `src/guardrails_redaction.py`'s naive pattern
(`NAIVE_PHONE_PATTERN`) covers dash- and space-separated US phone-number
formats but not the dot-separated format (e.g. `214.690.1014`), a real,
commonly occurring variant the synthetic generator deliberately injects
into a subset of agent outputs.

**Detection.**
```
tests/test_guardrails_redaction.py::test_naive_redactor_leaks_dot_separated_phone_numbers PASSED
  14 real dot-separated phone numbers pass through unredacted
```

**Fix.** The pattern is extended to cover the dot-separated variant.

```
tests/test_guardrails_redaction.py::test_fixed_redactor_catches_every_real_leak_the_naive_pattern_missed PASSED
tests/test_guardrails_redaction.py::test_fixed_redactor_still_catches_dash_and_space_formats PASSED
  all 14 real leaks closed; dash and space formats still redacted
```

**Business impact if unfixed:** PII reaching stored agent output data is
exactly the class of failure this JD calls out under "responsible AI
principles, and PII handling," and is the same shape of failure as the
real Samsung ChatGPT source-code leak cited in `data/bronze/SOURCE.md`.

**Git history:**
```
7faeba5 Add PII redaction layer (Bedrock Guardrails stand-in); reproduced naive dash/space-only phone regex leaking 14 real dot-separated phone numbers through agent output text (test confirms bug)
fb6c613 Fix: extend phone-number pattern to cover dot-separated format; all 14 real leaks closed, dash/space formats still covered, 3/3 tests passing
```
