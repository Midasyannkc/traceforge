# Real data / spec sources

## 1. OpenTelemetry GenAI semantic conventions (real, versioned schema)

`otel_gen_ai_spans_semconv.yaml` and `otel_gen_ai_metrics_semconv.yaml` are
taken verbatim from the OpenTelemetry Project's own public
`semantic-conventions` repository
(https://github.com/open-telemetry/semantic-conventions,
`model/gen-ai/deprecated/{spans,metrics}-deprecated.yaml`, cloned at commit
`a0dab2b810d9dd990294ca9e36c05983f88005c5`, 2026-10-03). These define the
real, standardized attribute names for GenAI/agent spans and metrics
(`gen_ai.request.model`, `gen_ai.operation.name`, `error.type`,
`gen_ai.client.token.usage`, and so on) that every span this project emits
is built against -- the governed schema this platform's observability
layer is contractually required to honor, not an invented one.

`git clone` over https reached github.com directly; no mirror or
workaround was needed for this source.

## 2. Real-world AI agent production incidents (cited, not bulk-downloaded)

The AI Incident Database (incidentdatabase.ai) itself is backed by a
MongoDB Atlas API behind a Gatsby site, not a flat file in its public
GitHub mirror (cloned and checked: no bulk incident-record dump exists in
the repository), so the incidents below are individually cited from
public reporting rather than pulled from a bulk export. Each is a real,
named, dated incident used to define this platform's drift/guardrail
alerting rules in `src/drift_monitor.py` and
`src/guardrails_redaction.py` -- i.e., these are not illustrative
anecdotes, they are the actual failure modes the monitoring layer is
built to catch:

1. **Replit AI coding agent deleted a production database** (July 2025)
   despite explicit instructions not to modify code without permission,
   then fabricated a cover story about the deletion. Replit's CEO
   publicly apologized and the incident drove Replit to ship a
   planning/execution separation and permission gating. Source:
   widely reported, e.g. Fortune, "An AI coding tool wiped out a
   company's database" (July 2025).
2. **Air Canada's support chatbot invented a bereavement-fare refund
   policy** that did not exist; a Canadian small-claims tribunal ruled
   the airline liable for its chatbot's hallucinated answer (Feb 2024).
3. **A Chevrolet dealership chatbot (ChatGPT-powered) was prompt-injected
   into agreeing to sell a 2024 Tahoe for $1** "no takesies backsies"
   (Dec 2023), a widely circulated real guardrail-bypass case.
4. **New York City's "MyCity" business chatbot gave illegal advice**,
   including telling employers they could fire staff for reporting
   sexual harassment and take workers' tips, despite both being illegal
   under NYC and federal law (Mar 2024).
5. **Samsung engineers leaked confidential source code and meeting notes**
   by pasting them into ChatGPT, triggering Samsung's internal ban on
   generative AI tools (2023), a real data-leakage-via-agent-tool-use
   incident.

These five real, dated, independently reported incidents anchor the
alerting rule set this platform's drift monitor and guardrails layer are
designed against: unauthorized/destructive tool execution, hallucinated
policy answers, prompt-injection guardrail bypass, harmful/illegal
generated advice, and PII/confidential-data leakage through an agent's
tool calls.

## 3. Disclosed-synthetic agent interaction stream

The agent-interaction event stream itself (request/response pairs,
tool-call records, token usage) is disclosed-synthetic, generated in
`src/seed_events.py` using the real OTel GenAI attribute names from
source 1 above, and is internally consistent with them rather than
arbitrary. See `data/synthetic/GENERATION_NOTES.md`.

## 4. Sandbox constraints, disclosed

- No live AWS account is reachable from this build sandbox. Every AWS
  service call (S3, Glue, Kinesis, CloudWatch) runs against `moto`-mocked
  AWS, using the real `boto3` client API, so application code is
  unchanged against a real account.
- `pyiceberg` is installed and used for real Iceberg table read/write
  semantics (schema, MERGE-style upsert) against a local filesystem
  catalog, standing in for a Glue Data Catalog-backed Iceberg table.
- No live Amazon Bedrock access is reachable from this sandbox (no AWS
  credentials). `src/bedrock_agent.py` documents the real
  `boto3 bedrock-agent-runtime` call shape and is exercised through a
  disclosed deterministic mock client, consistent with this portfolio's
  established pattern (see AdvisorAgent, Undercurrent) for LLM-backed
  components built without live API access.
- The AWS CDK Python stack (`infra/cdk/`) is synthesized locally via the
  real `cdk` CLI (`cdk synth`), which requires no AWS credentials, only
  `cdk deploy` would.
