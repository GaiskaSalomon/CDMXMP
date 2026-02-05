"""Data quality report generator."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from mobility_pulse.config import CDMX_BBOX, PROCESSED_DIR, REPORTS_DIR
from mobility_pulse.validate.schemas import point_schema, station_status_schema

LOGGER = logging.getLogger(__name__)


def _load_optional(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        LOGGER.warning("Missing processed file: %s", path)
        return None
    return pd.read_parquet(path)


def _bbox_out_of_bounds(df: pd.DataFrame) -> float:
    mask = (
        (df["lon"] < CDMX_BBOX["min_lon"])
        | (df["lon"] > CDMX_BBOX["max_lon"])
        | (df["lat"] < CDMX_BBOX["min_lat"])
        | (df["lat"] > CDMX_BBOX["max_lat"])
    )
    return float(mask.mean()) if len(df) else 0.0


def _dataset_summary(name: str, df: pd.DataFrame) -> list[str]:
    lines = [f"### {name}"]
    lines.append(f"- Rows: {len(df):,}")

    if "timestamp" in df.columns:
        ts_min = df["timestamp"].min()
        ts_max = df["timestamp"].max()
        lines.append(f"- Time coverage: {ts_min} to {ts_max}")

    missing_pct = df.isna().mean().sort_values(ascending=False).head(8)
    lines.append("- Missingness (top 8 columns):")
    for col, pct in missing_pct.items():
        lines.append(f"  - {col}: {pct:.2%}")

    dup_cols = []
    for col in df.columns:
        series = df[col].dropna()
        if series.empty:
            dup_cols.append(col)
            continue
        sample = series.iloc[0]
        if isinstance(sample, (list, dict, set, np.ndarray)):
            continue
        dup_cols.append(col)

    dup_rate = float(df[dup_cols].duplicated().mean()) if len(df) and dup_cols else 0.0
    lines.append(f"- Duplicate rate: {dup_rate:.2%}")

    if "lat" in df.columns and "lon" in df.columns:
        out_bounds = _bbox_out_of_bounds(df.dropna(subset=["lat", "lon"]))
        lines.append(f"- Out-of-bounds geo: {out_bounds:.2%}")

    return lines


def generate_report() -> Path:
    """Generate a markdown data-quality report."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / "data_quality.md"

    datasets = {
        "C5 Incidents": PROCESSED_DIR / "c5_incidents.parquet",
        "GTFS Stops": PROCESSED_DIR / "gtfs_stops.parquet",
        "ECOBICI RT": PROCESSED_DIR / "ecobici_rt.parquet",
        "ECOBICI Trips": PROCESSED_DIR / "ecobici_trips.parquet",
    }

    lines = ["# Data Quality Report", ""]

    for name, path in datasets.items():
        df = _load_optional(path)
        if df is None:
            lines.append(f"### {name}\n- Missing dataset")
            lines.append("")
            continue

        lines.extend(_dataset_summary(name, df))

        # Basic schema validation
        if {"lat", "lon"}.issubset(df.columns):
            try:
                point_schema.validate(df, lazy=True)
            except Exception as exc:
                lines.append(f"- Schema warnings: {exc}")

        if name == "ECOBICI RT":
            try:
                station_status_schema.validate(df, lazy=True)
            except Exception as exc:
                lines.append(f"- Station status warnings: {exc}")
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    LOGGER.info("Wrote %s", report_path)
    return report_path
