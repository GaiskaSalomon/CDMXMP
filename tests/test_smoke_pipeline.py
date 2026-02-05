"""Smoke tests for core pipeline pieces."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

import mobility_pulse.analytics.aggregates as aggregates
import mobility_pulse.analytics.ppi as ppi
import mobility_pulse.validate.quality_report as quality_report


def _write_parquet(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def test_build_analytics_and_ppi(tmp_path: Path, monkeypatch) -> None:
    processed = tmp_path / "processed"
    analytics = tmp_path / "analytics"
    reports = tmp_path / "reports"

    monkeypatch.setattr(aggregates, "PROCESSED_DIR", processed)
    monkeypatch.setattr(aggregates, "ANALYTICS_DIR", analytics)
    monkeypatch.setattr(ppi, "PROCESSED_DIR", processed)
    monkeypatch.setattr(ppi, "ANALYTICS_DIR", analytics)
    monkeypatch.setattr(quality_report, "PROCESSED_DIR", processed)
    monkeypatch.setattr(quality_report, "REPORTS_DIR", reports)

    c5_df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2024-01-01 08:00", "2024-01-01 09:00"]),
            "lat": [19.4, 19.41],
            "lon": [-99.1, -99.11],
            "zone_id": ["zone_a", "zone_a"],
            "source": ["c5", "c5"],
        }
    )
    gtfs_df = pd.DataFrame(
        {
            "lat": [19.4],
            "lon": [-99.1],
            "zone_id": ["zone_a"],
            "source": ["gtfs"],
        }
    )

    _write_parquet(processed / "c5_incidents.parquet", c5_df)
    _write_parquet(processed / "gtfs_stops.parquet", gtfs_df)

    aggregates.build_analytics()
    ppi_path = ppi.build_ppi()
    report_path = quality_report.generate_report()

    assert (analytics / "c5_hourly.parquet").exists()
    assert ppi_path is not None and ppi_path.exists()
    assert report_path.exists()