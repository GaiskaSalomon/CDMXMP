"""Standardization transforms."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from mobility_pulse.config import PROCESSED_DIR, RAW_DIR
from mobility_pulse.transform.geo import add_zone_id

LOGGER = logging.getLogger(__name__)


def _safe_read_csv(path: Path, **kwargs: object) -> pd.DataFrame | None:
    if not path.exists():
        LOGGER.warning("Missing file: %s", path)
        return None
    return pd.read_csv(path, **kwargs)


def standardize_c5() -> Path | None:
    raw_path = RAW_DIR / "c5" / "c5_incidents.csv"
    df = _safe_read_csv(raw_path)
    if df is None:
        return None

    # Common column guesses with priority ordering
    date_candidates = [c for c in df.columns if "fecha" in c.lower() or "date" in c.lower()]
    time_candidates = [c for c in df.columns if "hora" in c.lower() or "time" in c.lower()]

    def _pick(cols: list[str], preferred: list[str]) -> str | None:
        lower_map = {c.lower(): c for c in cols}
        for key in preferred:
            if key in lower_map:
                return lower_map[key]
        return cols[0] if cols else None

    lat_candidates = [
        c for c in df.columns if c.lower() in {"lat", "latitud", "latitude"} or c.lower().startswith("lat")
    ]
    lon_candidates = [
        c
        for c in df.columns
        if c.lower() in {"lon", "lng", "longitud", "longitude"} or c.lower().startswith("lon")
    ]

    ts_col = date_candidates[0] if date_candidates else None
    time_col = time_candidates[0] if time_candidates else None
    lat_col = _pick(lat_candidates, ["latitud", "latitude", "lat"])
    lon_col = _pick(lon_candidates, ["longitud", "longitude", "lon", "lng"])

    def _detect_dayfirst(series: pd.Series) -> bool:
        sample = series.dropna().astype(str).str.strip().head(50)
        if sample.empty:
            return True
        return not sample.str.match(r"^\d{4}-\d{2}-\d{2}$").any()

    dayfirst = _detect_dayfirst(df[ts_col]) if ts_col else True

    if ts_col and time_col:
        df["timestamp"] = pd.to_datetime(
            df[ts_col].astype(str).str.strip() + " " + df[time_col].astype(str).str.strip(),
            errors="coerce",
            dayfirst=dayfirst,
        )
    elif ts_col:
        df["timestamp"] = pd.to_datetime(df[ts_col], errors="coerce", dayfirst=dayfirst)
    else:
        df["timestamp"] = pd.NaT

    df["lat"] = pd.to_numeric(df[lat_col], errors="coerce") if lat_col else pd.NA
    df["lon"] = pd.to_numeric(df[lon_col], errors="coerce") if lon_col else pd.NA
    df["source"] = "c5"

    df = add_zone_id(df)

    out_path = PROCESSED_DIR / "c5_incidents.parquet"
    df.to_parquet(out_path, index=False)
    LOGGER.info("Wrote %s", out_path)
    return out_path


def standardize_gtfs() -> Path | None:
    stops_path = RAW_DIR / "gtfs" / "extracted" / "stops.txt"
    df = _safe_read_csv(stops_path)
    if df is None:
        return None

    df = df.rename(
        columns={
            "stop_lat": "lat",
            "stop_lon": "lon",
            "stop_id": "stop_id",
            "stop_name": "stop_name",
        }
    )
    df["timestamp"] = pd.NaT
    df["source"] = "gtfs"
    df = add_zone_id(df, lat_col="lat", lon_col="lon")

    out_path = PROCESSED_DIR / "gtfs_stops.parquet"
    df.to_parquet(out_path, index=False)
    LOGGER.info("Wrote %s", out_path)
    return out_path


def standardize_ecobici_rt() -> Path | None:
    raw_path = RAW_DIR / "ecobici" / "rt" / "parsed" / "station_snapshots.parquet"
    if not raw_path.exists():
        LOGGER.warning("Missing file: %s", raw_path)
        return None

    df = pd.read_parquet(raw_path)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        if hasattr(df["timestamp"].dt, "tz"):
            df["timestamp"] = df["timestamp"].dt.tz_localize(None)
    else:
        df["timestamp"] = pd.NaT
    df["lat"] = pd.to_numeric(df.get("lat"), errors="coerce")
    df["lon"] = pd.to_numeric(df.get("lon"), errors="coerce")
    df["source"] = "ecobici_rt"

    if "bikes_available" not in df.columns and "num_bikes_available" in df.columns:
        df["bikes_available"] = pd.to_numeric(df["num_bikes_available"], errors="coerce")
    if "docks_available" not in df.columns and "num_docks_available" in df.columns:
        df["docks_available"] = pd.to_numeric(df["num_docks_available"], errors="coerce")

    df = add_zone_id(df, lat_col="lat", lon_col="lon")

    out_path = PROCESSED_DIR / "ecobici_rt.parquet"
    df.to_parquet(out_path, index=False)
    LOGGER.info("Wrote %s", out_path)
    return out_path


def standardize_ecobici_trips() -> Path | None:
    raw_path = RAW_DIR / "ecobici" / "trips" / "ecobici_trips.csv"
    df = _safe_read_csv(raw_path)
    if df is None:
        return None

    # Common column guesses
    start_date = next((c for c in df.columns if "fecha_retiro" in c.lower()), None)
    start_time = next((c for c in df.columns if "hora_retiro" in c.lower()), None)
    end_date = next((c for c in df.columns if "fecha_arribo" in c.lower()), None)
    end_time = next((c for c in df.columns if "hora_arribo" in c.lower()), None)

    start_ts = next((c for c in df.columns if "start" in c.lower() and "time" in c.lower()), None)
    end_ts = next((c for c in df.columns if "end" in c.lower() and "time" in c.lower()), None)
    start_station = next(
        (c for c in df.columns if "estacion_retiro" in c.lower() or ("start" in c.lower() and "station" in c.lower())),
        None,
    )
    end_station = next(
        (c for c in df.columns if "estacionarribo" in c.lower() or ("end" in c.lower() and "station" in c.lower())),
        None,
    )

    if start_date and start_time:
        df["timestamp"] = pd.to_datetime(
            df[start_date].astype(str).str.strip() + " " + df[start_time].astype(str).str.strip(),
            errors="coerce",
            dayfirst=True,
        )
    elif start_ts:
        df["timestamp"] = pd.to_datetime(df[start_ts], errors="coerce")
    else:
        df["timestamp"] = pd.NaT

    if end_date and end_time:
        df["end_timestamp"] = pd.to_datetime(
            df[end_date].astype(str).str.strip() + " " + df[end_time].astype(str).str.strip(),
            errors="coerce",
            dayfirst=True,
        )
    elif end_ts:
        df["end_timestamp"] = pd.to_datetime(df[end_ts], errors="coerce")
    else:
        df["end_timestamp"] = pd.NaT

    df["start_station_id"] = df[start_station] if start_station else pd.NA
    df["end_station_id"] = df[end_station] if end_station else pd.NA
    df["source"] = "ecobici_trips"

    # Try to attach coordinates for zone assignment.
    start_lat = next(
        (
            c
            for c in df.columns
            if ("lat" in c.lower() and ("retiro" in c.lower() or "start" in c.lower()))
        ),
        None,
    )
    start_lon = next(
        (
            c
            for c in df.columns
            if ("lon" in c.lower() or "lng" in c.lower())
            and ("retiro" in c.lower() or "start" in c.lower())
        ),
        None,
    )
    end_lat = next(
        (
            c
            for c in df.columns
            if ("lat" in c.lower() and ("arribo" in c.lower() or "end" in c.lower()))
        ),
        None,
    )
    end_lon = next(
        (
            c
            for c in df.columns
            if ("lon" in c.lower() or "lng" in c.lower())
            and ("arribo" in c.lower() or "end" in c.lower())
        ),
        None,
    )

    df["lat"] = pd.to_numeric(df[start_lat], errors="coerce") if start_lat else pd.NA
    df["lon"] = pd.to_numeric(df[start_lon], errors="coerce") if start_lon else pd.NA
    df["end_lat"] = pd.to_numeric(df[end_lat], errors="coerce") if end_lat else pd.NA
    df["end_lon"] = pd.to_numeric(df[end_lon], errors="coerce") if end_lon else pd.NA

    if start_lat is None or start_lon is None:
        stations_path = PROCESSED_DIR / "ecobici_rt.parquet"
        if stations_path.exists() and "station_id" in df.columns:
            stations = pd.read_parquet(stations_path)
            if {"station_id", "lat", "lon"}.issubset(stations.columns):
                stations = (
                    stations[["station_id", "lat", "lon"]]
                    .dropna(subset=["station_id"])
                    .drop_duplicates("station_id")
                )
                stations["station_id"] = stations["station_id"].astype(str)
                df["start_station_id"] = df["start_station_id"].astype(str)
                df = df.merge(
                    stations.rename(columns={"lat": "start_lat", "lon": "start_lon"}),
                    left_on="start_station_id",
                    right_on="station_id",
                    how="left",
                )
                df = df.drop(columns=["station_id"], errors="ignore")
                if "start_lat" in df.columns:
                    df["lat"] = df["lat"].fillna(df["start_lat"])
                if "start_lon" in df.columns:
                    df["lon"] = df["lon"].fillna(df["start_lon"])

    if end_lat is None or end_lon is None:
        stations_path = PROCESSED_DIR / "ecobici_rt.parquet"
        if stations_path.exists() and "end_station_id" in df.columns:
            stations = pd.read_parquet(stations_path)
            if {"station_id", "lat", "lon"}.issubset(stations.columns):
                stations = (
                    stations[["station_id", "lat", "lon"]]
                    .dropna(subset=["station_id"])
                    .drop_duplicates("station_id")
                )
                stations["station_id"] = stations["station_id"].astype(str)
                df["end_station_id"] = df["end_station_id"].astype(str)
                df = df.merge(
                    stations.rename(columns={"lat": "end_lat", "lon": "end_lon"}),
                    left_on="end_station_id",
                    right_on="station_id",
                    how="left",
                )
                df = df.drop(columns=["station_id"], errors="ignore")

    df = add_zone_id(df, lat_col="lat", lon_col="lon")
    if "end_lat" in df.columns and "end_lon" in df.columns:
        df["zone_id_end"] = add_zone_id(df, lat_col="end_lat", lon_col="end_lon")[
            "zone_id"
        ]

    out_path = PROCESSED_DIR / "ecobici_trips.parquet"
    df.to_parquet(out_path, index=False)
    LOGGER.info("Wrote %s", out_path)
    return out_path


def standardize_gps() -> Path | None:
    raw_dir = RAW_DIR / "gps"
    if not raw_dir.exists():
        return None

    candidates = list(raw_dir.glob("gps_cdmx.*"))
    if not candidates:
        return None

    path = candidates[0]
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() == ".json":
        df = pd.read_json(path)
    elif path.suffix.lower() == ".geojson":
        try:
            import geopandas as gpd
        except ImportError:
            LOGGER.warning("geopandas not available for geojson GPS data")
            return None
        gdf = gpd.read_file(path)
        if "geometry" in gdf.columns:
            gdf["lon"] = gdf.geometry.x
            gdf["lat"] = gdf.geometry.y
        df = pd.DataFrame(gdf.drop(columns=["geometry"], errors="ignore"))
    else:
        LOGGER.warning("Unsupported GPS file format: %s", path)
        return None

    ts_col = next((c for c in df.columns if "time" in c.lower() or "fecha" in c.lower()), None)
    lat_col = next((c for c in df.columns if "lat" in c.lower()), None)
    lon_col = next((c for c in df.columns if "lon" in c.lower() or "lng" in c.lower()), None)

    df["timestamp"] = pd.to_datetime(df[ts_col], errors="coerce") if ts_col else pd.NaT
    df["lat"] = pd.to_numeric(df[lat_col], errors="coerce") if lat_col else pd.NA
    df["lon"] = pd.to_numeric(df[lon_col], errors="coerce") if lon_col else pd.NA
    df["source"] = "gps_cdmx"

    df = add_zone_id(df, lat_col="lat", lon_col="lon")

    out_path = PROCESSED_DIR / "gps_cdmx.parquet"
    df.to_parquet(out_path, index=False)
    LOGGER.info("Wrote %s", out_path)
    return out_path


def standardize_all() -> None:
    """Run all standardization steps."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    standardize_gtfs()
    standardize_c5()
    standardize_ecobici_rt()
    standardize_ecobici_trips()
    standardize_gps()
