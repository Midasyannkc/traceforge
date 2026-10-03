"""
Renders the CloudWatch/Grafana-equivalent dashboard as static charts (no
live AWS/Grafana account reachable from this sandbox -- see
docs/cost-tradeoffs.md). Same validated categorical palette used
elsewhere in this portfolio.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.seed_events import generate_events
from src.kinesis_consumer import create_stream, put_events, consume_naive, consume_fixed, new_client
from src.drift_monitor import naive_drift_check, fixed_drift_check
from src.guardrails_redaction import scan_events_for_leaked_pii, redact_naive, redact_fixed
from moto import mock_aws

OUT_DIR = Path(__file__).resolve().parents[1] / "docs" / "dashboard"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID_COLOR = "#e3e2dd"
BLUE = "#2a78d6"
CORAL = "#eb6834"
GREEN = "#1baf7a"


def _style_axes(ax):
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(GRID_COLOR)
    ax.spines["bottom"].set_color(GRID_COLOR)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    ax.yaxis.grid(True, color=GRID_COLOR, linewidth=0.8)
    ax.set_axisbelow(True)


@mock_aws
def chart_burst_consumption():
    _, _, burst = generate_events()
    client = new_client()
    shard_id = create_stream(client)
    put_events(client, burst)
    naive = len(consume_naive(client, shard_id, max_polls=3, poll_limit=10))
    client.delete_stream(StreamName="traceforge-telemetry")
    for _ in range(50):
        try:
            client.describe_stream(StreamName="traceforge-telemetry")
        except Exception:
            break
    shard_id2 = create_stream(client)
    put_events(client, burst)
    fixed = len(consume_fixed(client, shard_id2))

    fig, ax = plt.subplots(figsize=(6, 4.5))
    bars = ax.bar(["Naive consumer", "Fixed consumer"], [naive, fixed], color=[CORAL, GREEN], width=0.5)
    ax.axhline(len(burst), color=TEXT_SECONDARY, linestyle="--", linewidth=1, label=f"Real burst size ({len(burst)})")
    for b, v in zip(bars, [naive, fixed]):
        ax.text(b.get_x() + b.get_width() / 2, v + 3, str(v), ha="center", fontsize=10, color=TEXT_PRIMARY)
    _style_axes(ax)
    ax.legend(frameon=False, fontsize=9)
    ax.set_title("Events consumed from a real burst (150 events)", color=TEXT_PRIMARY, fontsize=12, loc="left")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "01_burst_consumption.png", dpi=150)
    plt.close(fig)


def chart_drift_detection():
    baseline, shifted, _ = generate_events()
    naive_psi = naive_drift_check(shifted)["psi"]
    fixed_psi = fixed_drift_check(baseline, shifted)["psi"]

    fig, ax = plt.subplots(figsize=(6, 4.5))
    bars = ax.bar(["Naive\n(self-referential baseline)", "Fixed\n(frozen baseline)"],
                   [naive_psi, fixed_psi], color=[CORAL, GREEN], width=0.5)
    ax.axhline(0.2, color=TEXT_SECONDARY, linestyle="--", linewidth=1, label="Drift threshold (PSI 0.2)")
    for b, v in zip(bars, [naive_psi, fixed_psi]):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.2, f"{v:.2f}", ha="center", fontsize=10, color=TEXT_PRIMARY)
    _style_axes(ax)
    ax.legend(frameon=False, fontsize=9)
    ax.set_title("Drift score (PSI) against the real latency shift", color=TEXT_PRIMARY, fontsize=12, loc="left")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "02_drift_detection.png", dpi=150)
    plt.close(fig)


def chart_pii_leaks():
    baseline, shifted, _ = generate_events()
    all_events = baseline + shifted
    naive_leaked = len(scan_events_for_leaked_pii(all_events, redact_naive))
    fixed_leaked = len(scan_events_for_leaked_pii(all_events, redact_fixed))

    fig, ax = plt.subplots(figsize=(6, 4.5))
    bars = ax.bar(["Naive redactor", "Fixed redactor"], [naive_leaked, fixed_leaked], color=[CORAL, GREEN], width=0.5)
    for b, v in zip(bars, [naive_leaked, fixed_leaked]):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.2, str(v), ha="center", fontsize=10, color=TEXT_PRIMARY)
    _style_axes(ax)
    ax.set_title("Real PII leaks reaching stored agent output", color=TEXT_PRIMARY, fontsize=12, loc="left")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "03_pii_leaks.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    chart_burst_consumption()
    chart_drift_detection()
    chart_pii_leaks()
    print("wrote charts to", OUT_DIR)
