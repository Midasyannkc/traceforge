from moto import mock_aws

from src.seed_events import generate_events
from src.kinesis_consumer import create_stream, put_events, consume_naive, consume_fixed, new_client


@mock_aws
def test_naive_consumer_drops_most_of_a_real_burst():
    _, _, burst = generate_events()
    client = new_client()
    shard_id = create_stream(client)
    put_events(client, burst)
    consumed = consume_naive(client, shard_id, max_polls=3, poll_limit=10)
    # BUG: 3 polls x 10 records = at most 30 of 150 burst events consumed
    assert len(consumed) == 30
    assert len(consumed) < len(burst)


@mock_aws
def test_fixed_consumer_drains_the_full_burst():
    _, _, burst = generate_events()
    client = new_client()
    shard_id = create_stream(client)
    put_events(client, burst)
    consumed = consume_fixed(client, shard_id)
    assert len(consumed) == len(burst)
