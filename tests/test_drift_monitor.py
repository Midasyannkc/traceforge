from src.seed_events import generate_events
from src.drift_monitor import naive_drift_check, fixed_drift_check


def test_naive_monitor_misses_real_drift_once_window_is_post_shift():
    _, shifted, _ = generate_events()
    result = naive_drift_check(shifted)
    # BUG: comparing shifted-vs-shifted (self-referential baseline) hides
    # the real latency shift that actually occurred relative to the true
    # pre-shift baseline
    assert result["drift_detected"] is False


def test_fixed_monitor_catches_the_same_real_drift_against_frozen_baseline():
    baseline, shifted, _ = generate_events()
    result = fixed_drift_check(baseline, shifted)
    assert result["drift_detected"] is True
    assert result["psi"] > naive_drift_check(shifted)["psi"]


def test_fixed_monitor_reports_no_drift_within_the_baseline_period_itself():
    baseline, _, _ = generate_events()
    mid = len(baseline) // 2
    result = fixed_drift_check(baseline[:mid], baseline[mid:])
    assert result["drift_detected"] is False
