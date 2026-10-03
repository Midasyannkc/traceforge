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
