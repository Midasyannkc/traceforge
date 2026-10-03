from pathlib import Path

from src.render_dashboard_charts import chart_burst_consumption, chart_drift_detection, chart_pii_leaks, OUT_DIR


def test_all_three_charts_render():
    chart_burst_consumption()
    chart_drift_detection()
    chart_pii_leaks()
    for name in ("01_burst_consumption.png", "02_drift_detection.png", "03_pii_leaks.png"):
        p = Path(OUT_DIR) / name
        assert p.exists() and p.stat().st_size > 0
