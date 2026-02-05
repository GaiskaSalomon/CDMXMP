"""Pandera schemas for validation."""

from __future__ import annotations

import pandera.pandas as pa
from pandera import Column, DataFrameSchema


point_schema = DataFrameSchema(
    {
        "timestamp": Column(pa.DateTime, nullable=True),
        "lat": Column(pa.Float, nullable=True, checks=pa.Check.in_range(-90, 90)),
        "lon": Column(pa.Float, nullable=True, checks=pa.Check.in_range(-180, 180)),
        "source": Column(pa.String, nullable=False),
    },
    strict=False,
)


station_status_schema = DataFrameSchema(
    {
        "bikes_available": Column(pa.Int, nullable=True, checks=pa.Check.ge(0)),
        "docks_available": Column(pa.Int, nullable=True, checks=pa.Check.ge(0)),
        "num_bikes_available": Column(pa.Int, nullable=True, checks=pa.Check.ge(0)),
        "num_docks_available": Column(pa.Int, nullable=True, checks=pa.Check.ge(0)),
    },
    strict=False,
)
