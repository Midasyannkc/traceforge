"""
Loads agent-interaction events into a real Iceberg table (via `pyiceberg`
against a local SQL catalog, standing in for a Glue Data Catalog-backed
Iceberg table on S3 -- see data/bronze/SOURCE.md). Demonstrates Incident 1:
a naive append-based loader double-writes every record on a job retry
after a transient failure; the fix uses Iceberg's real upsert on a natural
key so a retry after partial failure is idempotent.
"""
import os
import shutil
import tempfile

import pyarrow as pa
from pyiceberg.catalog.sql import SqlCatalog

SCHEMA = pa.schema([
    ("event_id", pa.string()),
    ("workflow", pa.string()),
    ("gen_ai_operation_name", pa.string()),
    ("gen_ai_request_model", pa.string()),
    ("latency_ms", pa.int64()),
    ("error_type", pa.string()),
])


def _to_arrow(events):
    return pa.table({
        "event_id": [e["event_id"] for e in events],
        "workflow": [e["workflow"] for e in events],
        "gen_ai_operation_name": [e["gen_ai.operation.name"] for e in events],
        "gen_ai_request_model": [e["gen_ai.request.model"] for e in events],
        "latency_ms": [e["latency_ms"] for e in events],
        "error_type": [e.get("error.type") for e in events],
    }, schema=SCHEMA)


def new_local_catalog(warehouse_dir=None):
    """Creates a fresh local Iceberg catalog (SQL catalog + filesystem
    warehouse), standing in for a Glue Data Catalog."""
    d = warehouse_dir or tempfile.mkdtemp(prefix="traceforge_iceberg_")
    catalog = SqlCatalog(
        "traceforge",
        **{"uri": f"sqlite:///{d}/catalog.db", "warehouse": f"file://{d}/warehouse"},
    )
    catalog.create_namespace("agent_platform")
    return catalog, d


def get_or_create_table(catalog):
    try:
        return catalog.load_table("agent_platform.agent_interactions")
    except Exception:
        return catalog.create_table("agent_platform.agent_interactions", schema=SCHEMA)


def load_naive(catalog, events, *, simulate_retry_after_partial_write=False):
    """
    NAIVE: append-only write. A job that fails partway through and gets
    retried from the start has no way to know which records already
    landed, so a retry simply re-appends everything -- real duplicate
    rows in the Iceberg table.
    """
    table = get_or_create_table(catalog)
    table.append(_to_arrow(events))
    if simulate_retry_after_partial_write:
        # the "retry from the top" that a naive orchestration step takes
        # after an upstream timeout, once the first attempt's write had
        # already landed
        table.append(_to_arrow(events))
    return table


def load_fixed(catalog, events):
    """
    FIX: Iceberg's real upsert on the natural key (event_id). A retry
    after a partial or full write is a no-op for rows already present,
    verified below in tests/test_glue_iceberg_loader.py.
    """
    table = get_or_create_table(catalog)
    table.upsert(_to_arrow(events), join_cols=["event_id"])
    return table


def row_count(table):
    return table.scan().to_pandas().shape[0]


def cleanup(warehouse_dir):
    shutil.rmtree(warehouse_dir, ignore_errors=True)
