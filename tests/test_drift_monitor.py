from src.seed_events import generate_events
from src.drift_monitor import naive_drift_check


def test_naive_monitor_misses_real_drift_once_window_is_post_shift():
    _, shifted, _ = generate_events()
    result = naive_drift_check(shifted)
    # BUG: comparing shifted-vs-shifted (self-referential baseline) hides
    # the real latency shift that actually occurred relative to the true
    # pre-shift baseline
    assert result["drift_detected"] is False
