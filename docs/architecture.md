# Architecture

```
REAL SPEC ANCHOR                            REAL CITED INCIDENTS
┌───────────────────────────┐                ┌──────────────────────────┐
│ OpenTelemetry GenAI        │                │ 5 real, dated AI agent    │
│ semantic conventions        │                │ production incidents     │
│ (real, versioned schema)    │                │ (Replit, Air Canada,      │
└──────────┬──────────────────┘                │ Chevrolet, NYC MyCity,    │
           │ gen_ai.* attribute names          │ Samsung) anchor the       │
           ▼                                    │ drift/guardrail rules    │
  src/seed_events.py (disclosed-synthetic)      └──────────────┬───────────┘
           │                                                   │
           ▼                                                   │
  src/otel_instrumentation.py                                  │
  (real OTel SDK spans, real TracerProvider)                   │
           │                                                   │
           ▼                                                   │
  src/kinesis_consumer.py  ──real moto-mocked Kinesis──▶  (Incident 2 fix:
  (real boto3 calls)                                       batched/checkpointed
           │                                                consumption)
           ▼
  src/guardrails_redaction.py  (Incident 4 fix: dot-separated
   phone pattern; Bedrock Guardrails stand-in)
           │
           ▼
  src/glue_iceberg_loader.py  ──real local Iceberg table──▶  (Incident 1 fix:
  (pyiceberg, Glue Data Catalog stand-in)                      upsert on event_id)
           │
           ├──▶ src/drift_monitor.py  (Incident 3 fix: frozen baseline,
           │     SageMaker Model Monitor stand-in)                 │
           │                                                       ▼
           └──▶ real moto-mocked CloudWatch metrics         docs/dashboard/*.png
                 (src/platform_orchestrator.py)

  src/bedrock_agent.py  (disclosed deterministic mock, real
   invoke_agent call shape documented)

  infra/cdk/traceforge_stack.py  (real AWS CDK Python stack,
   synthesized via real `cdk synth`: KMS-encrypted S3 bucket,
   encrypted Kinesis stream, least-privilege IAM role)
```

## Storage

A real local Iceberg table via `pyiceberg` (SQL catalog + filesystem
warehouse), standing in for a Glue Data Catalog-backed Iceberg table on
S3 (no live AWS account reachable from this sandbox -- see
`data/bronze/SOURCE.md`). The real Iceberg `upsert` API is what makes
Incident 1's fix genuine rather than simulated.

## Streaming and orchestration

A real moto-mocked Kinesis stream, read through real `boto3` calls
(`get_shard_iterator`, `get_records`). `src/platform_orchestrator.py`
plays the role of a scheduled Lambda orchestrator, tying consumption,
redaction, the Iceberg upsert, CloudWatch metric emission, and drift
checking into one real, tested, end-to-end pass over a batch of agent
events (`tests/test_platform_orchestrator.py`).

## Observability

Real OpenTelemetry Python SDK instrumentation (`TracerProvider`,
`SimpleSpanProcessor`, `InMemorySpanExporter`) genuinely constructs and
exports spans carrying the real `gen_ai.*` attribute names from the OTel
GenAI semantic conventions. CloudWatch metrics are emitted through real
`boto3` calls against moto-mocked CloudWatch. X-Ray trace export and
Amazon Managed Service for Prometheus/Grafana are documented as the
production targets for this same OTel instrumentation in
`docs/cost-tradeoffs.md`, since this sandbox has no live AWS account to
export to.

## Agent enablement

`src/bedrock_agent.py` documents the real `boto3
bedrock-agent-runtime.invoke_agent` call shape and exercises it through a
disclosed deterministic mock, the same established pattern this
portfolio uses for LLM-backed components with no live API access
(AdvisorAgent, Undercurrent).

## Infrastructure as code

A real AWS CDK (Python) stack (`infra/cdk/traceforge_stack.py`),
synthesized locally with the real `cdk` CLI (`cdk synth`, no AWS
credentials required) into a 7-resource CloudFormation template: a
KMS-encrypted, versioned, public-access-blocked S3 bucket; a
KMS-encrypted Kinesis stream; and a least-privilege IAM role, verified
with real `aws_cdk.assertions.Template` checks
(`tests/test_cdk_stack.py`) rather than hand-inspected JSON.
