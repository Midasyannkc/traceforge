from src.seed_events import generate_events
from src.guardrails_redaction import scan_events_for_leaked_pii, redact_naive, redact_fixed


def test_naive_redactor_leaks_dot_separated_phone_numbers():
    baseline, shifted, _ = generate_events()
    leaked = scan_events_for_leaked_pii(baseline + shifted, redact_naive)
    # BUG: the naive pattern covers dash/space phone formats only; real
    # dot-separated numbers pass through unredacted
    assert len(leaked) > 0


def test_fixed_redactor_catches_every_real_leak_the_naive_pattern_missed():
    baseline, shifted, _ = generate_events()
    all_events = baseline + shifted
    naive_leaked = scan_events_for_leaked_pii(all_events, redact_naive)
    assert len(naive_leaked) > 0
    fixed_leaked = scan_events_for_leaked_pii(all_events, redact_fixed)
    assert len(fixed_leaked) == 0


def test_fixed_redactor_still_catches_dash_and_space_formats():
    assert "[REDACTED PHONE]" in redact_fixed("call 214-690-1014 now")
    assert "[REDACTED PHONE]" in redact_fixed("call 214 690 1014 now")
    assert "[REDACTED PHONE]" in redact_fixed("call 214.690.1014 now")
