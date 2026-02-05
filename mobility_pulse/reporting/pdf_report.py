"""Report generation for CDMX Mobility Pulse (PDF + HTML + Markdown)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from mobility_pulse.config import ANALYTICS_DIR, REPORTS_DIR


def _load(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


def _safe_text(value: object) -> str:
    if value is None:
        return "n/a"
    return str(value)


def _write_plot(fig: go.Figure, path: Path) -> bool:
    try:
        fig.write_image(str(path), scale=2)
        return True
    except Exception:
        return False


def _build_charts(output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    charts: dict[str, Path] = {}

    c5_monthly = _load(ANALYTICS_DIR / "c5_monthly.parquet")
    c5_dow_total = _load(ANALYTICS_DIR / "c5_dow_total.parquet")
    access = _load(ANALYTICS_DIR / "accessibility_zones.parquet")
    pressure = _load(ANALYTICS_DIR / "c5_pressure.parquet")
    anomalies = _load(ANALYTICS_DIR / "c5_anomalies.parquet")

    if not c5_monthly.empty:
        total = c5_monthly.groupby("month", dropna=False)["count"].sum().reset_index()
        fig = px.line(total, x="month", y="count", title="C5 incidents by month")
        chart_path = output_dir / "c5_monthly.png"
        if _write_plot(fig, chart_path):
            charts["c5_monthly"] = chart_path

    if not c5_dow_total.empty:
        fig = px.bar(c5_dow_total, x="day_of_week", y="count", title="Incidents by day of week")
        chart_path = output_dir / "c5_dow.png"
        if _write_plot(fig, chart_path):
            charts["c5_dow"] = chart_path

        if not access.empty and "travel_time_min" in access.columns:
            bucket_counts = access["iso_bucket"].value_counts().reindex(
                ["<=5", "5-10", "10-15", "15-30", "30-60", "60+"], fill_value=0
            )
            bucket_df = bucket_counts.reset_index()
            bucket_df.columns = ["bucket", "count"]
            fig = px.bar(
                bucket_df,
                x="bucket",
                y="count",
                title="Walking minutes to nearest stop (proxy)",
            )
            fig.update_layout(xaxis_title="Minutes", yaxis_title="Zones")
            chart_path = output_dir / "iso_bucket.png"
            if _write_plot(fig, chart_path):
                charts["iso_bucket"] = chart_path

    if not pressure.empty:
        top5 = pressure.sort_values("risk_z", ascending=False).head(10)
        fig = px.bar(top5, x="zone_id", y="risk_z", title="Top risk zones")
        chart_path = output_dir / "risk_top.png"
        if _write_plot(fig, chart_path):
            charts["risk_top"] = chart_path

        heat = pressure.copy()
        centers = heat["zone_id"].apply(lambda cell: None)
        try:
            import h3

            centers = heat["zone_id"].apply(lambda cell: h3.cell_to_latlng(cell) if cell else None)
        except Exception:
            centers = heat["zone_id"].apply(lambda cell: None)
        heat["lat"] = centers.apply(lambda x: x[0] if x else pd.NA)
        heat["lon"] = centers.apply(lambda x: x[1] if x else pd.NA)
        heat = heat.dropna(subset=["lat", "lon"])
        if not heat.empty and "risk_z" in heat.columns:
            fig = go.Figure()
            fig.add_trace(
                go.Scattermap(
                    lat=heat["lat"],
                    lon=heat["lon"],
                    mode="markers",
                    marker=dict(
                        size=8,
                        color=heat["risk_z"],
                        colorscale="Reds",
                        opacity=0.85,
                        showscale=True,
                    ),
                    text=heat["zone_id"],
                    hovertemplate="Zone: %{text}<br>Risk z: %{marker.color:.2f}<extra></extra>",
                )
            )
            fig.update_layout(
                map_style="open-street-map",
                map_zoom=10,
                map_center=dict(lon=heat["lon"].mean(), lat=heat["lat"].mean()),
                height=520,
                margin=dict(l=0, r=0, t=0, b=0),
            )
            chart_path = output_dir / "risk_map.png"
            if _write_plot(fig, chart_path):
                charts["risk_map"] = chart_path

    if not access.empty:
        heat = access.copy()
        centers = heat["zone_id"].apply(lambda cell: None)
        try:
            import h3

            centers = heat["zone_id"].apply(lambda cell: h3.cell_to_latlng(cell) if cell else None)
        except Exception:
            centers = heat["zone_id"].apply(lambda cell: None)
        heat["lat"] = centers.apply(lambda x: x[0] if x else pd.NA)
        heat["lon"] = centers.apply(lambda x: x[1] if x else pd.NA)
        heat = heat.dropna(subset=["lat", "lon"])
        if not heat.empty:
            fig = go.Figure()
            fig.add_trace(
                go.Scattermap(
                    lat=heat["lat"],
                    lon=heat["lon"],
                    mode="markers",
                    marker=dict(
                        size=8,
                        color=heat["access_score"],
                        colorscale="Blues",
                        opacity=0.85,
                        showscale=True,
                    ),
                    text=heat["zone_id"],
                    hovertemplate="Zone: %{text}<br>Access score: %{marker.color:.2f}<extra></extra>",
                )
            )
            fig.update_layout(
                map_style="open-street-map",
                map_zoom=10,
                map_center=dict(lon=heat["lon"].mean(), lat=heat["lat"].mean()),
                height=520,
                margin=dict(l=0, r=0, t=0, b=0),
            )
            chart_path = output_dir / "access_map.png"
            if _write_plot(fig, chart_path):
                charts["access_map"] = chart_path

    return charts


def _build_narrative() -> list[str]:
    pressure = _load(ANALYTICS_DIR / "c5_pressure.parquet")
    access = _load(ANALYTICS_DIR / "accessibility_zones.parquet")
    anomalies = _load(ANALYTICS_DIR / "c5_anomalies.parquet")

    narrative = []
    if not pressure.empty:
        top = pressure.sort_values("risk_z", ascending=False).head(1)
        if not top.empty:
            narrative.append(
                f"Highest safety pressure in zone {top['zone_id'].iloc[0]} (risk z-score {top['risk_z'].iloc[0]:.2f})."
            )
    if not access.empty:
        low = access.sort_values("access_score", ascending=True).head(1)
        if not low.empty:
            narrative.append(
                f"Lowest access score in zone {low['zone_id'].iloc[0]} (access {low['access_score'].iloc[0]:.2f})."
            )
    if not anomalies.empty:
        spike = anomalies.sort_values("zscore", ascending=False).head(1)
        if not spike.empty:
            narrative.append(
                f"Incident spike on {spike['date'].iloc[0]} (+{spike['zscore'].iloc[0]:.2f} sigma)."
            )
    return narrative


def generate_pdf_report(output_path: Path | None = None) -> Path:
    """Generate a PDF report with charts and interpretive text."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.pdfgen import canvas
    except ImportError as exc:
        raise RuntimeError("reportlab is required for PDF generation. Install it with `pip install reportlab`.") from exc
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output = output_path or (REPORTS_DIR / "mobility_report.pdf")
    assets_dir = REPORTS_DIR / "assets"
    charts = _build_charts(assets_dir)
    narrative = _build_narrative()

    c = canvas.Canvas(str(output), pagesize=letter)
    width, height = letter

    # Cover page (corporate style)
    c.setFillColorRGB(0.04, 0.08, 0.12)
    c.rect(0, height - 2.5 * inch, width, 2.5 * inch, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(1 * inch, height - 1.2 * inch, "CDMX Mobility Pulse")
    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, height - 1.55 * inch, "Executive Mobility Report")
    c.setFont("Helvetica", 9)
    c.drawString(1 * inch, height - 1.85 * inch, "Generated automatically from open data analytics.")
    c.setFillColorRGB(0, 0, 0)
    c.showPage()

    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, height - 1 * inch, "Executive summary")
    y = height - 1.4 * inch
    c.setFont("Helvetica", 10)
    for line in narrative:
        c.drawString(1.1 * inch, y, f"- {_safe_text(line)}")
        y -= 0.22 * inch
    c.showPage()

    # One-page executive summary
    c.setFont("Helvetica-Bold", 18)
    c.drawString(1 * inch, height - 1 * inch, "Executive Summary (1 page)")
    c.setFont("Helvetica", 10)
    y = height - 1.5 * inch
    for line in narrative:
        c.drawString(1.1 * inch, y, f"- {_safe_text(line)}")
        y -= 0.22 * inch

    # KPI strip
    c.setFont("Helvetica-Bold", 11)
    c.drawString(1 * inch, y - 0.1 * inch, "Key KPIs")
    y -= 0.4 * inch
    c.setFont("Helvetica", 10)
    pressure = _load(ANALYTICS_DIR / "c5_pressure.parquet")
    access = _load(ANALYTICS_DIR / "accessibility_zones.parquet")
    anomalies = _load(ANALYTICS_DIR / "c5_anomalies.parquet")
    risk_val = pressure["risk_z"].max() if not pressure.empty else None
    access_val = access["access_score"].mean() if not access.empty else None
    spike_val = anomalies["zscore"].max() if not anomalies.empty else None
    kpis = [
        ("Top risk z-score", risk_val, "higher"),
        ("Avg access score", access_val, "higher"),
        ("Max spike sigma", spike_val, "higher"),
    ]
    for label, val, direction in kpis:
        if val is None:
            color = (0.6, 0.6, 0.6)
        else:
            if label == "Avg access score":
                if val >= 0.6:
                    color = (0.16, 0.65, 0.37)  # green
                elif val >= 0.4:
                    color = (0.95, 0.62, 0.13)  # amber
                else:
                    color = (0.86, 0.2, 0.2)    # red
            else:
                if val >= 2.0:
                    color = (0.86, 0.2, 0.2)
                elif val >= 1.0:
                    color = (0.95, 0.62, 0.13)
                else:
                    color = (0.16, 0.65, 0.37)

        c.setFillColorRGB(*color)
        c.circle(1.1 * inch, y + 3, 4, stroke=0, fill=1)
        c.setFillColorRGB(0, 0, 0)
        display = f"{val:.2f}" if val is not None else "n/a"
        c.drawString(1.25 * inch, y, f"{label}: {display}")
        y -= 0.22 * inch

    if "risk_map" in charts:
        c.drawImage(str(charts["risk_map"]), 1 * inch, y - 3.2 * inch, width=6.5 * inch, height=3.0 * inch)
    c.showPage()

    y = height - 1 * inch
    for _, chart_path in charts.items():
        if y < 2.5 * inch:
            c.showPage()
            y = height - 1 * inch
        c.drawImage(str(chart_path), 1 * inch, y - 3.5 * inch, width=6.5 * inch, height=3.2 * inch)
        y -= 3.7 * inch

    c.save()
    return output


def generate_markdown_report(output_path: Path | None = None) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output = output_path or (REPORTS_DIR / "mobility_report.md")
    assets_dir = REPORTS_DIR / "assets"
    charts = _build_charts(assets_dir)
    narrative = _build_narrative()

    lines = [
        "# CDMX Mobility Pulse Report",
        "",
        "## Executive summary",
    ]
    lines.extend([f"- {_safe_text(line)}" for line in narrative] or ["- n/a"])
    lines.append("")
    lines.append("## Charts")
    for name, path in charts.items():
        rel = Path("assets") / path.name
        lines.append(f"### {name.replace('_', ' ').title()}")
        lines.append(f"![{name}]({rel.as_posix()})")
        lines.append("")

    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def generate_html_report(output_path: Path | None = None) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output = output_path or (REPORTS_DIR / "mobility_report.html")
    assets_dir = REPORTS_DIR / "assets"
    charts = _build_charts(assets_dir)
    narrative = _build_narrative()

    chart_blocks = "\n".join(
        f"<h3>{name.replace('_', ' ').title()}</h3><img src='assets/{path.name}' style='max-width:100%;'/>"
        for name, path in charts.items()
    )
    narrative_blocks = "".join(f"<li>{_safe_text(line)}</li>" for line in narrative) or "<li>n/a</li>"

    html = f"""
    <html>
    <head><title>CDMX Mobility Pulse Report</title></head>
    <body style="font-family: Arial, sans-serif; margin: 24px;">
      <h1>CDMX Mobility Pulse Report</h1>
      <h2>Executive summary</h2>
      <ul>{narrative_blocks}</ul>
      <h2>Charts</h2>
      {chart_blocks}
    </body>
    </html>
    """
    output.write_text(html, encoding="utf-8")
    return output


def generate_report_bundle() -> dict[str, Path]:
    """Generate PDF + Markdown + HTML reports."""
    outputs: dict[str, Path] = {}
    try:
        outputs["pdf"] = generate_pdf_report()
    except RuntimeError:
        # PDF optional if reportlab is missing
        pass
    outputs["markdown"] = generate_markdown_report()
    outputs["html"] = generate_html_report()
    return outputs
