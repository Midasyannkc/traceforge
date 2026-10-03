"""
Latency-distribution drift detector, standing in for SageMaker Model
Monitor's drift-monitoring role against this platform's agent latency
and error-rate telemetry (see data/bronze/SOURCE.md).

Demonstrates Incident 3: the real production anti-pattern of a monitor
that re-derives its "baseline" from whatever recent window it is handed,
instead of anchoring to a frozen reference baseline captured before any
drift occurred. Once the pipeline has advanced into the shifted period,
a self-referential baseline compares shifted data against itself and
reports no drift, even though the underlying distribution genuinely
moved. The fix persists a frozen baseline captured once, during the
known-good period, and always compares against that.
"""
import math

PSI_DRIFT_THRESHOLD = 0.2  # industry rule-of-thumb: PSI > 0.2 is significant drift


def _bucket_edges(values, n_buckets=10):
    s = sorted(values)
    edges = [s[int(len(s) * i / n_buckets)] for i in range(n_buckets)]
    edges.append(s[-1] + 1)
    return edges


def compute_psi(baseline_values, comparison_values, n_buckets=10):
    """Real Population Stability Index between two latency distributions."""
    edges = _bucket_edges(baseline_values, n_buckets)

    def bucket_fractions(values):
        counts = [0] * n_buckets
        for v in values:
            for i in range(n_buckets):
                if edges[i] <= v < edges[i + 1] or (i == n_buckets - 1 and v >= edges[i]):
                    counts[i] += 1
                    break
        total = max(len(values), 1)
        return [max(c / total, 1e-6) for c in counts]

    base_frac = bucket_fractions(baseline_values)
    comp_frac = bucket_fractions(comparison_values)
    return sum((c - b) * math.log(c / b) for b, c in zip(base_frac, comp_frac))


def naive_drift_check(recent_window_events):
    """
    NAIVE: derives "baseline" from the first half of whatever window it is
    handed, and "comparison" from the second half of that same window.
    This looks reasonable in isolation, but once production has advanced
    past the shift point and this function is called on a recent window
    that is entirely post-shift, both halves are drawn from the already-
    shifted distribution -- the comparison is shifted-vs-shifted, so PSI
    stays near zero and real drift is missed.
    """
    mid = len(recent_window_events) // 2
    baseline = [e["latency_ms"] for e in recent_window_events[:mid]]
    comparison = [e["latency_ms"] for e in recent_window_events[mid:]]
    psi = compute_psi(baseline, comparison)
    return {"psi": psi, "drift_detected": psi > PSI_DRIFT_THRESHOLD}

