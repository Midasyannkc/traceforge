from src.seed_events import generate_events
from src.glue_iceberg_loader import (
    new_local_catalog, load_naive, load_fixed, row_count, cleanup,
)


def test_naive_loader_duplicates_rows_on_retry_after_partial_write():
    baseline, _, _ = generate_events()
    events = baseline[:50]
    catalog, warehouse_dir = new_local_catalog()
    try:
        table = load_naive(catalog, events, simulate_retry_after_partial_write=True)
        # BUG: a retry after the first write already landed doubles every row
        assert row_count(table) == len(events) * 2
    finally:
        cleanup(warehouse_dir)


def test_fixed_loader_upsert_makes_retry_a_no_op():
    baseline, _, _ = generate_events()
    events = baseline[:50]
    catalog, warehouse_dir = new_local_catalog()
    try:
        load_fixed(catalog, events)
        table = load_fixed(catalog, events)  # retry: same events again
        assert row_count(table) == len(events)
    finally:
        cleanup(warehouse_dir)


def test_fixed_loader_handles_a_real_mixed_retry_overlap():
    baseline, _, _ = generate_events()
    first_batch = baseline[:30]
    second_batch = baseline[20:60]  # overlaps first_batch by 10 real events
    catalog, warehouse_dir = new_local_catalog()
    try:
        load_fixed(catalog, first_batch)
        table = load_fixed(catalog, second_batch)
        assert row_count(table) == 60  # union, no duplicates on the 10 overlapping ids
    finally:
        cleanup(warehouse_dir)
