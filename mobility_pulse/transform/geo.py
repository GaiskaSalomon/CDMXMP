"""Geospatial helpers and H3 zoning."""

from __future__ import annotations

import geopandas as gpd
import pandas as pd
import h3
from shapely.geometry import Point

from mobility_pulse.config import DEFAULT_H3_RESOLUTION


def to_geodataframe(
    df: pd.DataFrame, lat_col: str = "lat", lon_col: str = "lon"
) -> gpd.GeoDataFrame:
    """Convert a DataFrame with lat/lon columns to a GeoDataFrame.

    Creates Point geometries from coordinate columns and sets CRS to EPSG:4326 (WGS84).

    Args:
        df: Input DataFrame with latitude and longitude columns.
        lat_col: Name of the latitude column (default: "lat").
        lon_col: Name of the longitude column (default: "lon").

    Returns:
        GeoDataFrame with Point geometries in EPSG:4326 coordinate system.
        Original DataFrame columns are preserved.

    Example:
        >>> df = pd.DataFrame({"lat": [19.43, 19.44], "lon": [-99.13, -99.14]})
        >>> gdf = to_geodataframe(df)
        >>> gdf.crs
        <Geographic 2D CRS: EPSG:4326>
    """
    geometry = [Point(xy) for xy in zip(df[lon_col], df[lat_col])]
    return gpd.GeoDataFrame(df.copy(), geometry=geometry, crs="EPSG:4326")


def add_zone_id(
    df: pd.DataFrame,
    lat_col: str = "lat",
    lon_col: str = "lon",
    resolution: int | None = None,
) -> pd.DataFrame:
    """Assign H3 hexagonal zone identifiers to rows with valid coordinates.

    Uses the H3 spatial indexing system to convert lat/lon coordinates into
    hexagonal cell IDs. Handles both old (h3-py < 4.0) and new H3 API versions.

    Args:
        df: Input DataFrame with latitude and longitude columns.
        lat_col: Name of the latitude column (default: "lat").
        lon_col: Name of the longitude column (default: "lon").
        resolution: H3 resolution level 0-15. Higher = smaller hexagons.
            Default uses config.DEFAULT_H3_RESOLUTION (typically 9 ≈ 180m edge).

    Returns:
        DataFrame with added 'zone_id' column containing H3 cell strings.
        Rows with invalid coordinates (NaN, out of range) get None for zone_id.

    Example:
        >>> df = pd.DataFrame({"lat": [19.432, None], "lon": [-99.133, -99.14]})
        >>> df = add_zone_id(df, resolution=9)
        >>> df["zone_id"].iloc[0]
        '89283082833ffff'
        >>> df["zone_id"].iloc[1]  # None due to missing lat
        None

    Note:
        Resolution 9 produces hexagons ~174m edge length (~0.1 km² area),
        suitable for urban mobility analysis at neighborhood scale.
    """
    res = resolution or DEFAULT_H3_RESOLUTION

    def _to_h3(lat: float, lon: float) -> str | None:
        if pd.isna(lat) or pd.isna(lon):
            return None
        try:
            if hasattr(h3, "geo_to_h3"):
                return h3.geo_to_h3(lat, lon, res)
            return h3.latlng_to_cell(lat, lon, res)
        except Exception:
            return None

    df = df.copy()
    df["zone_id"] = [
        _to_h3(lat, lon) for lat, lon in zip(df[lat_col], df[lon_col], strict=False)
    ]
    return df
