# Cost & Architecture Trade-offs

## Data lake: Iceberg on S3 vs. a traditional Hive table

Agent-interaction records arrive with evolving schemas as new agent
workflows and tool types are added (the JD's own single-pilot-to-
multi-agent scaling story). Iceberg's schema evolution and hidden
partitioning avoid the full-table rewrites a Hive-style table would need
on every schema change, at the cost of needing a catalog service (Glue
Data Catalog in production) that a flat S3-prefix layout would not.
`pyiceberg`'s real `upsert` API, exercised in Incident 1's fix, is the
feature a naive append-only Parquet-on-S3 layout cannot offer without
hand-rolled compaction.

**Production sizing:** at a few million agent interactions/day, a
single-digit-TB Iceberg table on S3 Standard, queried via Athena with
partition pruning on date, stays well under $200/month in storage plus
pay-per-query Athena cost, versus a comparable always-on Redshift
cluster running continuously whether queried or not.

## Streaming: Kinesis vs. MSK

Kinesis was chosen for this build over MSK (Managed Kafka) because the
ingestion pattern here is a single logical stream per environment with
moderate, bursty throughput (agent-interaction events, not a
high-partition-count multi-topic event mesh), which is exactly Kinesis's
sweet spot: no cluster to size or patch, shard-based scaling, and
pay-per-shard-hour billing that tracks actual load. MSK's advantage
(Kafka ecosystem compatibility, very high partition counts, cross-region
MirrorMaker) only pays off once there are many topics and consumer
groups across teams, which this single-platform observability pipeline
does not yet have.

**Production sizing:** one Kinesis shard handles up to 1,000 records/sec
or 1MB/sec; a few shards comfortably cover the burst pattern (Incident 2)
modeled in this build, at roughly $0.015/shard-hour plus a small
per-million-records PUT charge, well under $50/month.

## Observability: OpenTelemetry + CloudWatch/X-Ray vs. a third-party SaaS APM

OpenTelemetry was chosen as the instrumentation layer (not a
vendor-specific SDK) specifically so the same spans emitted in
`src/otel_instrumentation.py` can export to CloudWatch, X-Ray, or Amazon
Managed Service for Prometheus/Grafana without re-instrumenting
application code -- the OTel Collector handles the fan-out. A
third-party APM SaaS (Datadog, New Relic) offers a more polished UI out
of the box but locks instrumentation to its proprietary SDK and adds a
per-host/per-trace licensing cost that scales with exactly the traffic
this platform is meant to observe. This sandbox has no live AWS account
to export real spans to CloudWatch/X-Ray against, so that export step is
documented rather than demonstrated; the span-generation and attribute
contract (the part application code actually depends on) is real and
tested.

## Drift monitoring: a custom PSI monitor vs. SageMaker Model Monitor

A real, from-scratch PSI (Population Stability Index) implementation
was used in `src/drift_monitor.py` rather than standing up SageMaker
Model Monitor directly, since the latter requires a live SageMaker
endpoint and a baselining job this sandbox cannot run. The PSI formula,
threshold (0.2, the standard industry rule-of-thumb for significant
drift), and the frozen-vs-self-referential baseline failure mode fixed
in Incident 3 are the real mechanics SageMaker Model Monitor implements
internally; this build demonstrates understanding of that mechanism
directly rather than only configuring a managed wrapper around it.

## Agent enablement: Bedrock Agents vs. a self-hosted agent framework

Amazon Bedrock Agents (with Knowledge Bases and Guardrails) is the right
choice for an AWS-native enterprise deployment specifically because it
keeps PII/guardrail enforcement, retrieval grounding, and model
invocation inside one IAM/KMS security boundary, rather than stitching
together a self-hosted LangGraph/Strands orchestration layer plus a
separate vector store plus a separate guardrails library, each with its
own access-control surface to audit. The trade-off is less flexibility
in agent-orchestration logic than a self-hosted framework offers; for a
regulated-enterprise client engagement (this JD's actual context), the
single security boundary is usually the right trade.

## Cost optimization: storage, query, compute, and model usage

- **Storage:** Iceberg's columnar Parquet files plus partition pruning
  keep Athena/Glue query cost proportional to data actually scanned, not
  table size.
- **Query:** partitioning the Iceberg table by date (not implemented in
  this build's small local demonstration table, but the documented
  production layout) keeps a single day's dashboard query from scanning
  the full historical table.
- **Compute:** Kinesis shard count and Lambda concurrency both scale with
  real traffic rather than being provisioned for peak year-round, the
  same elasticity argument made in this portfolio's other serverless
  builds (GlacierFlow, CoverageLedger).
- **Model usage:** every span records `gen_ai.usage.input_tokens` and
  `gen_ai.usage.output_tokens` using the real OTel attribute names,
  which is exactly the data a per-workflow cost-attribution dashboard
  would aggregate, the direct answer to this JD's "cost optimization...
  across storage, query, compute, and model usage" requirement.
