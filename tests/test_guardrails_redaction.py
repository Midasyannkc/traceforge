from src.seed_events import generate_events
from src.guardrails_redaction import scan_events_for_leaked_pii, redact_naive


def test_naive_redactor_leaks_dot_separated_phone_numbers():
    baseline, shifted, _ = generate_events()
    leaked = scan_events_for_leaked_pii(baseline + shifted, redact_naive)
    # BUG: the naive pattern covers dash/space phone formats only; real
    # dot-separated numbers pass through unredacted
    assert len(leaked) > 0
