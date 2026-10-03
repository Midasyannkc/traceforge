# Coding Standards & Review Guidelines

Followed throughout this repository's git history:

1. **One concern per module.** Event generation (`seed_events.py`),
   instrumentation (`otel_instrumentation.py`), streaming
   (`kinesis_consumer.py`), the data lake (`glue_iceberg_loader.py`),
   drift monitoring (`drift_monitor.py`), PII redaction
   (`guardrails_redaction.py`), agent enablement (`bedrock_agent.py`),
   and orchestration (`platform_orchestrator.py`) are kept in separate
   files so a change to one doesn't require touching the others.
2. **Every claimed behavior gets a pinned test against real library
   calls.** Iceberg's `upsert`, Kinesis's `get_records`/
   `MillisBehindLatest`, CloudWatch's `put_metric_data`, and CDK's
   `Template` assertions are all exercised through their real APIs, not
   hand-rolled stand-ins, so a regression in actual behavior is caught.
3. **Fixes are proven, not asserted.** Every incident in
   `docs/incidents.md` has a before-state commit (bug reproduced, test
   failing) and a separate after-state commit (fix applied, test
   passing) -- never a single commit claiming both.
4. **No silent fallbacks.** A missing live dependency (a real AWS
   account, live Bedrock access, a bulk AI Incident Database export) is
   disclosed in `data/bronze/SOURCE.md`, not quietly faked without a
   note.
5. **Idempotent by default.** The Iceberg loader's `upsert` on a natural
   key is the default production path (`load_fixed`), not an opt-in.
6. **A fix is verified against a harder case than the one that exposed
   the bug.** The Iceberg fix is verified against a genuine
   partially-overlapping retry batch, not just an exact repeat; the
   drift-monitor fix is verified to report no drift within the baseline
   period itself, not just to flag the known shift.
7. **Security properties are asserted, not eyeballed.** The CDK stack's
   least-privilege claim is checked by a real test scanning every IAM
   policy statement for wildcard actions, rather than a human reading
   the generated CloudFormation JSON once.
8. **Commit messages state the verification, not just the change** --
   e.g. "19/19 tests passing" or the exact PSI figure -- so the git log
   itself is a verification trail.
