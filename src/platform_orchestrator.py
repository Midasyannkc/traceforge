"""
Ties the platform together the way a scheduled Lambda orchestrator would:
drain the Kinesis backlog (fixed consumer), redact PII (fixed pattern),
write to the Iceberg data lake (fixed idempotent upsert), emit real
CloudWatch metrics, and run the drift check against the frozen baseline.
Every AWS call is real boto3 against moto-mocked services (see
data/bronze/SOURCE.md).
"""
import json
import statistics

import boto3

from src.kinesis_consumer import create_stream, put_events, consume_fixed, new_client as new_kinesis_client
from src.glue_iceberg_loader import new_local_catalog, load_fixed, row_count
from src.guardrails_redaction import redact_fixed
from src.drift_monitor import fixed_drift_check

NAMESPACE = "TraceForge/AgentPlatform"


def new_cloudwatch_client(region_name="us-east-1"):
    return boto3.client("cloudwatch", region_name=region_name)


def put_latency_metric(cw_client, p95_latency_ms):
    cw_client.put_metric_data(
        Namespace=NAMESPACE,
        MetricData=[{
            "MetricName": "p95LatencyMs",
            "Value": p95_latency_ms,
            "Unit": "Milliseconds",
        }],
    )


def run_pipeline(kinesis_client, cw_client, iceberg_catalog, frozen_baseline_events, incoming_events):
    """One orchestration pass over a batch of incoming agent events."""
    shard_id = create_stream(kinesis_client)
    put_events(kinesis_client, incoming_events)
    records = consume_fixed(kinesis_client, shard_id)
    decoded = [json.loads(r["Data"]) for r in records]

    for e in decoded:
        if e.get("output_text"):
            e["output_text"] = redact_fixed(e["output_text"])

    table = load_fixed(iceberg_catalog, decoded)

    latencies = [e["latency_ms"] for e in decoded]
    p95 = statistics.quantiles(latencies, n=100)[94] if len(latencies) >= 20 else max(latencies)
    put_latency_metric(cw_client, p95)

    drift = fixed_drift_check(frozen_baseline_events, decoded)

    return {
        "events_consumed": len(decoded),
        "rows_in_table": row_count(table),
        "p95_latency_ms": p95,
        "drift": drift,
    }
