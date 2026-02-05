"""Priority/Policy Readiness Index (PPI) calculations."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from mobility_pulse.config import ANALYTICS_DIR, PROCESSED_DIR

LOGGER = logging.getLogger(__name__)


def _load_optional(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        LOGGER.warning("Missing processed file: %s", path)
        return None
    return pd.read_parquet(path)


def _zscore(series: pd.Series) -> pd.Series:
    mean = series.mean()
    std = series.std(ddof=0)
    if std == 0 or pd.isna(std):
        return pd.Series([0.0] * len(series), index=series.index)
    return (series - mean) / std


def build_ppi() -> Path | None:
    """Compute Priority/Policy Readiness Index (PPI) scores by zone.

    PPI combines incident frequency and exposure to identify zones requiring
    policy attention. Higher PPI indicates zones with high incidents relative
    to transit/mobility exposure.

    Formula:
        PPI = 0.7 × incidents_z + 0.3 × exposure_z

    Where:
        - incidents_z: Z-score of incident counts per zone
        - exposure_z: Z-score of exposure metric (GTFS stops or bike trips)

    Returns:
        Path to saved analytics/ppi_zones.parquet file, or None if insufficient data.
        Output columns:
            - zone_id: H3 hexagon identifier
            - incidents: Count of incidents in zone
            - exposure: Count of transit stops or trips in zone
            - incidents_z: Standardized incident score
            - exposure_z: Standardized exposure score
            - ppi: Combined priority index
            - exposure_source: Data source used ('gtfs_stops', 'ecobici_trips', or 'none')

    Example:
        >>> ppi_path = build_ppi()
        >>> ppi_df = pd.read_parquet(ppi_path)
        >>> top_zones = ppi_df.nlargest(5, 'ppi')
        >>> print(top_zones[['zone_id', 'ppi']])

    Note:
        Requires processed c5_incidents.parquet. Exposure uses GTFS stops if available,
        falls back to ECOBICI trips, or sets exposure to 0 if neither exists.
    """
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)

    incidents = _load_optional(PROCESSED_DIR / "c5_incidents.parquet")
    if incidents is None or "zone_id" not in incidents.columns:
        LOGGER.warning("No incidents data available for PPI")
        return None

    incidents_counts = (
        incidents.groupby("zone_id", dropna=False).size().rename("incidents")
    )

    exposure_source = None
    exposure_df = _load_optional(PROCESSED_DIR / "gtfs_stops.parquet")
    if exposure_df is not None and "zone_id" in exposure_df.columns:
        exposure_counts = (
            exposure_df.groupby("zone_id", dropna=False).size().rename("exposure")
        )
        exposure_source = "gtfs_stops"
    else:
        trips_df = _load_optional(PROCESSED_DIR / "ecobici_trips.parquet")
        if trips_df is not None and "zone_id" in trips_df.columns:
            exposure_counts = (
                trips_df.groupby("zone_id", dropna=False).size().rename("exposure")
            )
            exposure_source = "ecobici_trips"
        else:
            exposure_counts = pd.Series(dtype=float, name="exposure")

    table = pd.concat([incidents_counts, exposure_counts], axis=1).fillna(0)
    table["incidents_z"] = _zscore(table["incidents"])
    table["exposure_z"] = (
        _zscore(table["exposure"]) if not table["exposure"].empty else 0
    )
    table["ppi"] = 0.7 * table["incidents_z"] + 0.3 * table["exposure_z"]
    table["exposure_source"] = exposure_source or "none"
    table = table.reset_index().rename(columns={"index": "zone_id"})

    out_path = ANALYTICS_DIR / "ppi_zones.parquet"
    table.to_parquet(out_path, index=False)
    LOGGER.info("Wrote %s", out_path)
    return out_path
