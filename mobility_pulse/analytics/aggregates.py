"""Aggregations for dashboard analytics."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import h3

from mobility_pulse.config import ANALYTICS_DIR, PROCESSED_DIR

LOGGER = logging.getLogger(__name__)


def _load_optional(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        LOGGER.warning("Missing processed file: %s", path)
        return None
    return pd.read_parquet(path)


def _add_time_parts(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.day_name()
    df["month"] = df["timestamp"].dt.to_period("M").astype(str)
    return df


def _count_by(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    return df.groupby(by, dropna=False).size().reset_index(name="count")


def build_analytics() -> dict[str, Path]:
    """Build aggregated analytics tables."""
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)

    datasets = {
        "c5": _load_optional(PROCESSED_DIR / "c5_incidents.parquet"),
        "ecobici_trips": _load_optional(PROCESSED_DIR / "ecobici_trips.parquet"),
    }

    output_paths: dict[str, Path] = {}

    # Accessibility proxy from GTFS stops (Phase 2 MVP)
    stops_df = _load_optional(PROCESSED_DIR / "gtfs_stops.parquet")
    c5_df = _load_optional(PROCESSED_DIR / "c5_incidents.parquet")
    if stops_df is not None and "zone_id" in stops_df.columns:
        stops_counts = (
            stops_df.groupby("zone_id", dropna=False).size().reset_index(name="stops")
        )
        zone_ids = set(stops_counts["zone_id"].dropna().astype(str))
        if c5_df is not None and "zone_id" in c5_df.columns:
            zone_ids |= set(c5_df["zone_id"].dropna().astype(str))
        if zone_ids:
            zones_df = pd.DataFrame({"zone_id": sorted(zone_ids)})
            stops_counts = zones_df.merge(
                stops_counts, on="zone_id", how="left"
            ).fillna({"stops": 0})

            max_stops = stops_counts["stops"].max() or 1
            stops_counts["stops_norm"] = stops_counts["stops"] / max_stops

            stop_zone_set = set(stops_counts.loc[stops_counts["stops"] > 0, "zone_id"])

            def _grid_disk(cell: str, k: int) -> set[str]:
                if hasattr(h3, "grid_disk"):
                    return set(h3.grid_disk(cell, k))
                return set(h3.k_ring(cell, k))

            def _edge_length_m(resolution: int) -> float:
                if hasattr(h3, "average_hexagon_edge_length"):
                    return float(h3.average_hexagon_edge_length(resolution, unit="m"))
                if hasattr(h3, "hexagon_edge_length"):
                    return float(h3.hexagon_edge_length(resolution, unit="m"))
                # Fallback to known average edge lengths (meters) by resolution.
                edge_m = [
                    1107712.591,
                    418676.0055,
                    158244.6558,
                    59810.85794,
                    22606.3794,
                    8544.408276,
                    3229.482772,
                    1220.629759,
                    461.354684,
                    174.375668,
                    65.907807,
                    24.910561,
                    9.415526,
                    3.559893,
                    1.348575,
                    0.509713,
                ]
                if 0 <= resolution < len(edge_m):
                    return float(edge_m[resolution])
                return 0.0

            distances = []
            rings = []
            max_k = 6
            for cell in stops_counts["zone_id"]:
                if cell in stop_zone_set:
                    rings.append(0)
                    distances.append(0.0)
                    continue
                found_k = None
                for k in range(1, max_k + 1):
                    if _grid_disk(cell, k) & stop_zone_set:
                        found_k = k
                        break
                if found_k is None:
                    found_k = max_k + 1
                rings.append(found_k)
                res = (
                    h3.get_resolution(cell)
                    if hasattr(h3, "get_resolution")
                    else h3.h3_get_resolution(cell)
                )
                distances.append(found_k * _edge_length_m(int(res)))

            stops_counts["nearest_stop_ring"] = rings
            stops_counts["access_distance_m"] = distances

            max_dist = stops_counts["access_distance_m"].max() or 1
            stops_counts["distance_norm"] = 1 - (
                stops_counts["access_distance_m"] / max_dist
            )
            walk_speed_m_min = 80.0
            stops_counts["travel_time_min"] = (
                stops_counts["access_distance_m"] / walk_speed_m_min
            )
            stops_counts["iso_bucket"] = pd.cut(
                stops_counts["travel_time_min"],
                bins=[-0.1, 5, 10, 15, 30, 60, float("inf")],
                labels=["<=5", "5-10", "10-15", "15-30", "30-60", "60+"],
            ).astype(str)

            stops_counts["access_score"] = (0.7 * stops_counts["stops_norm"]) + (
                0.3 * stops_counts["distance_norm"]
            )
            mean = stops_counts["access_score"].mean()
            std = stops_counts["access_score"].std(ddof=0) or 1
            stops_counts["access_z"] = (stops_counts["access_score"] - mean) / std

            access_path = ANALYTICS_DIR / "accessibility_zones.parquet"
            stops_counts.to_parquet(access_path, index=False)
            output_paths["accessibility_zones"] = access_path

            # Impact index: high incidents + low access
            if c5_df is not None and "zone_id" in c5_df.columns:
                inc_counts = (
                    c5_df.groupby("zone_id", dropna=False)
                    .size()
                    .reset_index(name="incidents")
                )
                impact = stops_counts.merge(
                    inc_counts, on="zone_id", how="left"
                ).fillna({"incidents": 0})
                inc_mean = impact["incidents"].mean()
                inc_std = impact["incidents"].std(ddof=0) or 1
                impact["incidents_z"] = (impact["incidents"] - inc_mean) / inc_std
                impact["impact_score"] = impact["incidents_z"] * (
                    1 - impact["access_score"]
                )
                impact_path = ANALYTICS_DIR / "impact_zones.parquet"
                impact.to_parquet(impact_path, index=False)
                output_paths["impact_zones"] = impact_path

    for name, df in datasets.items():
        if df is None or "timestamp" not in df.columns:
            continue
        df = _add_time_parts(df)
        if "zone_id" not in df.columns:
            df["zone_id"] = None
        df["date"] = pd.to_datetime(df["timestamp"], errors="coerce").dt.date

        hourly = _count_by(df, ["zone_id", "hour"])
        daily = _count_by(df, ["zone_id", "day_of_week"])
        monthly = _count_by(df, ["zone_id", "month"])
        zone_counts = _count_by(df, ["zone_id"])
        hour_total = _count_by(df, ["hour"])
        dow_total = _count_by(df, ["day_of_week"])
        zone_daily = _count_by(df, ["zone_id", "date"])

        hourly_path = ANALYTICS_DIR / f"{name}_hourly.parquet"
        daily_path = ANALYTICS_DIR / f"{name}_dow.parquet"
        monthly_path = ANALYTICS_DIR / f"{name}_monthly.parquet"
        zone_path = ANALYTICS_DIR / f"{name}_zones.parquet"
        hour_total_path = ANALYTICS_DIR / f"{name}_hourly_total.parquet"
        dow_total_path = ANALYTICS_DIR / f"{name}_dow_total.parquet"
        zone_daily_path = ANALYTICS_DIR / f"{name}_zone_daily.parquet"

        hourly.to_parquet(hourly_path, index=False)
        daily.to_parquet(daily_path, index=False)
        monthly.to_parquet(monthly_path, index=False)
        zone_counts.to_parquet(zone_path, index=False)
        hour_total.to_parquet(hour_total_path, index=False)
        dow_total.to_parquet(dow_total_path, index=False)
        zone_daily.to_parquet(zone_daily_path, index=False)

        output_paths[f"{name}_hourly"] = hourly_path
        output_paths[f"{name}_dow"] = daily_path
        output_paths[f"{name}_monthly"] = monthly_path
        output_paths[f"{name}_zones"] = zone_path
        output_paths[f"{name}_hourly_total"] = hour_total_path
        output_paths[f"{name}_dow_total"] = dow_total_path
        output_paths[f"{name}_zone_daily"] = zone_daily_path

        if name == "c5":
            daily_counts = (
                df.assign(date=pd.to_datetime(df["timestamp"], errors="coerce").dt.date)
                .groupby("date", dropna=False)
                .size()
                .reset_index(name="count")
            )
            if not daily_counts.empty:
                mean = daily_counts["count"].mean()
                std = daily_counts["count"].std(ddof=0) or 1
                daily_counts["zscore"] = (daily_counts["count"] - mean) / std
                daily_path = ANALYTICS_DIR / "c5_daily.parquet"
                anomalies_path = ANALYTICS_DIR / "c5_anomalies.parquet"
                daily_counts.to_parquet(daily_path, index=False)
                daily_counts.sort_values("zscore", ascending=False).head(14).to_parquet(
                    anomalies_path, index=False
                )
                output_paths["c5_daily"] = daily_path
                output_paths["c5_anomalies"] = anomalies_path

            stops_df = _load_optional(PROCESSED_DIR / "gtfs_stops.parquet")
            if stops_df is not None and "zone_id" in stops_df.columns:
                stops_counts = (
                    stops_df.groupby("zone_id", dropna=False).size().rename("stops")
                )
                inc_counts = zone_counts.set_index("zone_id")["count"].rename(
                    "incidents"
                )
                pressure = pd.concat([inc_counts, stops_counts], axis=1).fillna(0)
                pressure["incidents_per_stop"] = pressure["incidents"] / (
                    pressure["stops"] + 1
                )
                mean = pressure["incidents_per_stop"].mean()
                std = pressure["incidents_per_stop"].std(ddof=0) or 1
                pressure["risk_z"] = (pressure["incidents_per_stop"] - mean) / std
                pressure = pressure.reset_index()
                pressure_path = ANALYTICS_DIR / "c5_pressure.parquet"
                pressure.to_parquet(pressure_path, index=False)
                output_paths["c5_pressure"] = pressure_path

    # GPS-like proxy analytics using C5 incidents (public CDMX data)
    c5_df = datasets.get("c5")
    if c5_df is not None and "timestamp" in c5_df.columns:
        c5_df = _add_time_parts(c5_df)
        gps_like_monthly = _count_by(c5_df, ["month"])
        gps_like_hourly = _count_by(c5_df, ["hour"])
        gps_like_dow = _count_by(c5_df, ["day_of_week"])
        gps_like_zones = _count_by(c5_df, ["zone_id"])
        gps_like_zone_hour = _count_by(c5_df, ["zone_id", "hour"])

        gps_like_monthly_path = ANALYTICS_DIR / "gps_like_monthly.parquet"
        gps_like_hourly_path = ANALYTICS_DIR / "gps_like_hourly.parquet"
        gps_like_dow_path = ANALYTICS_DIR / "gps_like_dow.parquet"
        gps_like_zones_path = ANALYTICS_DIR / "gps_like_zones.parquet"
        gps_like_zone_hour_path = ANALYTICS_DIR / "gps_like_zone_hour.parquet"
        gps_like_risk_path = ANALYTICS_DIR / "gps_like_risk.parquet"
        gps_like_od_path = ANALYTICS_DIR / "gps_like_od.parquet"

        gps_like_monthly.to_parquet(gps_like_monthly_path, index=False)
        gps_like_hourly.to_parquet(gps_like_hourly_path, index=False)
        gps_like_dow.to_parquet(gps_like_dow_path, index=False)
        gps_like_zones.to_parquet(gps_like_zones_path, index=False)
        gps_like_zone_hour.to_parquet(gps_like_zone_hour_path, index=False)

        output_paths["gps_like_monthly"] = gps_like_monthly_path
        output_paths["gps_like_hourly"] = gps_like_hourly_path
        output_paths["gps_like_dow"] = gps_like_dow_path
        output_paths["gps_like_zones"] = gps_like_zones_path
        output_paths["gps_like_zone_hour"] = gps_like_zone_hour_path

        # Risk ranking proxy: incidents per stop with z-score
        stops_df = _load_optional(PROCESSED_DIR / "gtfs_stops.parquet")
        if stops_df is not None and "zone_id" in stops_df.columns:
            stops_counts = (
                stops_df.groupby("zone_id", dropna=False).size().rename("stops")
            )
            inc_counts = gps_like_zones.set_index("zone_id")["count"].rename(
                "incidents"
            )
            risk = pd.concat([inc_counts, stops_counts], axis=1).fillna(0)
            risk["incidents_per_stop"] = risk["incidents"] / (risk["stops"] + 1)
            mean = risk["incidents_per_stop"].mean()
            std = risk["incidents_per_stop"].std(ddof=0) or 1
            risk["risk_z"] = (risk["incidents_per_stop"] - mean) / std
            risk = risk.reset_index().rename(columns={"index": "zone_id"})
            risk.to_parquet(gps_like_risk_path, index=False)
            output_paths["gps_like_risk"] = gps_like_risk_path

        # Synthetic OD matrix from top zones (outer product of counts)
        top = gps_like_zones.sort_values("count", ascending=False).head(12)
        if not top.empty:
            top["weight"] = top["count"] / top["count"].sum()
            od = top.merge(top, how="cross", suffixes=("_o", "_d"))
            od["flow"] = (
                (od["weight_o"] * od["weight_d"] * top["count"].sum())
                .round(0)
                .astype(int)
            )
            od = od[["zone_id_o", "zone_id_d", "flow"]]
            od.to_parquet(gps_like_od_path, index=False)
            output_paths["gps_like_od"] = gps_like_od_path

    return output_paths
