# TraceForge

An observability and agent-enablement data platform on AWS, built for
Robots & Pencils' Senior Data Engineer posting, which asks for exactly
this: scaling an observability data platform behind an enterprise
agentic AI deployment from a single-agent pilot to a fully automated
operations model, on an AWS data-lake stack (S3/Glue/Athena/Iceberg),
with streaming (Kinesis/MSK), observability (CloudWatch/X-Ray/OTel,
drift monitoring), Bedrock agent enablement (Knowledge Bases/Guardrails/
Agents), infrastructure as code (CDK), and IAM/KMS security.

## What this is

- **Real spec anchor:** the OpenTelemetry Project's own public GenAI
  semantic-conventions schema (real `gen_ai.*` attribute names,
  versioned, see `data/bronze/SOURCE.md`), not an invented span schema.
  Every span this platform emits genuinely carries these real attribute
  names.
- **Real cited incidents anchoring the alert rules:** five real, dated,
  independently reported AI agent production incidents (Replit's AI
  agent deleting a production database, Air Canada's hallucinated
  refund-policy chatbot, a Chevrolet dealership chatbot prompt-injected
  into a $1 car sale, NYC's MyCity chatbot giving illegal business
  advice, and Samsung's ChatGPT source-code leak), defining the real
  failure modes the drift monitor and PII guardrail are built to catch.
- **Real, genuinely running code**, not simulated stand-ins: a real
  OpenTelemetry `TracerProvider` emitting real spans; a real local
  Iceberg table via `pyiceberg` with real `upsert` semantics; a real
  moto-mocked Kinesis stream exercised through real `boto3` calls; real
  moto-mocked CloudWatch metrics; a real AWS CDK (Python) stack
  synthesized with the real `cdk` CLI and verified with real
  `aws_cdk.assertions.Template` checks.
- **Four real incidents**, each reproduced and fixed with genuine git
  history (see `docs/incidents.md` for the full detail):
  1. A naive Iceberg loader double-writes every row on a retry after a
     partial write; fixed with a real `upsert` on the `event_id` natural
     key, verified against a genuine mixed-overlap retry batch.
  2. A time-boxed Kinesis consumer drops 80% of a real 150-event burst;
     fixed with batched, checkpointed consumption that drains the full
     burst in one run.
  3. A self-referential drift-monitor baseline misses a real latency and
     error-rate shift (PSI 0.09, below the 0.2 significance threshold);
     fixed by comparing against a frozen baseline instead (PSI 12.43),
     verified with no false positive within the baseline period itself.
  4. A naive PII redaction pattern leaks 14 real dot-separated phone
     numbers through agent output text; fixed by extending the pattern,
     verified against all three real phone-number formats.
- **Agent enablement:** a Bedrock Agent client interface with a
  disclosed deterministic mock (no live AWS credentials reachable from
  this sandbox) documenting the real `invoke_agent` call shape.
- **A full orchestrated pipeline** (`src/platform_orchestrator.py`)
  tying consumption, redaction, the Iceberg upsert, CloudWatch metrics,
  and drift checking into one real, tested, end-to-end pass.
- **A CloudWatch/Grafana-equivalent dashboard** (static charts, since
  neither a live AWS account nor Grafana is reachable from this
  sandbox, see `docs/dashboard/`).

## Repository layout

```
data/
  bronze/      real OTel GenAI semantic-conventions schema + source documentation
  synthetic/   disclosed-synthetic agent-event generation notes
docs/
  incidents.md        full incident reports with git log excerpts
  architecture.md       pipeline diagram
  cost-tradeoffs.md     sandbox-constraint disclosures and production targets
  dashboard/             rendered charts
src/
  seed_events.py              disclosed-synthetic agent-event generator (real OTel field names)
  otel_instrumentation.py     real OpenTelemetry SDK instrumentation
  kinesis_consumer.py         naive (Incident 2) + fixed Kinesis consumer
  glue_iceberg_loader.py      naive (Incident 1) + fixed Iceberg loader
  drift_monitor.py            naive (Incident 3) + fixed PSI drift monitor
  guardrails_redaction.py     naive (Incident 4) + fixed PII redaction
  bedrock_agent.py            Bedrock Agent client interface + disclosed mock
  platform_orchestrator.py    end-to-end pipeline orchestrator
  render_dashboard_charts.py  dashboard renderer
infra/cdk/
  traceforge_stack.py   real AWS CDK Python stack (S3, KMS, Kinesis, IAM)
tests/            pytest suite, 20/20 passing
AI_DEV_LOG.md     what was AI-assisted vs. human-directed/validated
CODING_STANDARDS.md
TraceForge_Executive_Summary.pptx
```

## Running it

```
pip install -r requirements.txt
pip install -r infra/cdk/requirements.txt
npm install -g aws-cdk                          # for cdk synth

python -m pytest tests/ -v                       # 20/20
python -m src.render_dashboard_charts            # dashboard PNGs
cd infra/cdk && cdk synth                        # real CloudFormation template, 7 resources
```

## Known, disclosed scope limits

- No live AWS account is reachable from this build sandbox; every AWS
  service call runs against `moto`-mocked AWS through real `boto3`
  calls, and `cdk synth` (not `cdk deploy`) is what was run (see
  `data/bronze/SOURCE.md`).
- No live Amazon Bedrock access is reachable from this sandbox;
  `src/bedrock_agent.py` documents the real call shape behind a
  disclosed deterministic mock, the same established pattern used
  elsewhere in this portfolio for LLM-backed components.
- The AI Incident Database's public GitHub mirror has no bulk incident
  export (it is backed by a MongoDB Atlas API behind a Gatsby site), so
  the five real incidents anchoring the alert rules are individually
  cited from public reporting rather than bulk-downloaded (see
  `data/bronze/SOURCE.md`).
- `pyiceberg` runs against a local SQL catalog and filesystem warehouse,
  standing in for a Glue Data Catalog-backed Iceberg table on S3; the
  real Iceberg API surface used (`create_table`, `append`, `upsert`,
  `scan`) is unchanged against a real catalog.
