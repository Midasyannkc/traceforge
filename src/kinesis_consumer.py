"""
Streams agent-telemetry events through a real Kinesis stream (moto-mocked,
real boto3 calls -- see data/bronze/SOURCE.md). Demonstrates Incident 2: a
naive, time-boxed consumer (a fixed number of poll iterations with a small
per-call Limit, modeling a Lambda-style poller with a hard time budget)
falls behind under a real burst load and silently leaves a large fraction
of the backlog unread -- those events never reach CloudWatch metrics. The
fix batches reads with a larger Limit and loops until the shard is caught
up (MillisBehindLatest == 0), so a burst is fully drained within one run.
"""
import json
import time

import boto3

STREAM_NAME = "traceforge-telemetry"


def create_stream(client, shard_count=1):
    client.create_stream(StreamName=STREAM_NAME, ShardCount=shard_count)
    for _ in range(50):
        desc = client.describe_stream(StreamName=STREAM_NAME)
        if desc["StreamDescription"]["StreamStatus"] == "ACTIVE":
            return desc["StreamDescription"]["Shards"][0]["ShardId"]
        time.sleep(0.05)
    raise RuntimeError("stream never became ACTIVE")


def put_events(client, events):
    for e in events:
        client.put_record(
            StreamName=STREAM_NAME,
            Data=json.dumps(e).encode("utf-8"),
            PartitionKey=e["event_id"],
        )


def consume_naive(client, shard_id, *, max_polls=3, poll_limit=10):
    """
    NAIVE: a fixed, small number of poll iterations with a small Limit
    per call -- a time-boxed poller that simply stops after max_polls
    regardless of whether the shard is caught up. Under a real burst, the
    remaining records are left in the stream and never observed by this
    run, i.e. silently dropped from this run's metrics.
    """
    it = client.get_shard_iterator(
        StreamName=STREAM_NAME, ShardId=shard_id, ShardIteratorType="TRIM_HORIZON"
    )["ShardIterator"]
    consumed = []
    for _ in range(max_polls):
        resp = client.get_records(ShardIterator=it, Limit=poll_limit)
        consumed.extend(resp["Records"])
        it = resp["NextShardIterator"]
        if not resp["Records"]:
            break
    return consumed


def consume_fixed(client, shard_id, *, poll_limit=200, max_iterations=1000):
    """
    FIX: batched reads with a larger Limit, looping until the shard
    reports it is caught up (MillisBehindLatest == 0) or the iterator
    exhausts, so a burst within a single run is fully drained rather than
    cut off by an arbitrary iteration count.
    """
    it = client.get_shard_iterator(
        StreamName=STREAM_NAME, ShardId=shard_id, ShardIteratorType="TRIM_HORIZON"
    )["ShardIterator"]
    consumed = []
    for _ in range(max_iterations):
        resp = client.get_records(ShardIterator=it, Limit=poll_limit)
        consumed.extend(resp["Records"])
        it = resp["NextShardIterator"]
        if resp["MillisBehindLatest"] == 0 and not resp["Records"]:
            break
    return consumed


def new_client(region_name="us-east-1"):
    return boto3.client("kinesis", region_name=region_name)
