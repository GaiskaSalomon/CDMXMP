"""ECOBICI historical trips ingest logic."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import requests

from mobility_pulse.config import RAW_DIR, get_dataset_url

LOGGER = logging.getLogger(__name__)


def ingest_ecobici_trips(limit_rows: int | None = None) -> Path:
    """Download ECOBICI trips CSV (optionally limit rows)."""
    url = get_dataset_url("ecobici_trips")
    raw_dir = RAW_DIR / "ecobici" / "trips"
    raw_dir.mkdir(parents=True, exist_ok=True)

    csv_path = raw_dir / "ecobici_trips.csv"
    LOGGER.info("Downloading ECOBICI trips from %s", url)
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with csv_path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)

    if limit_rows:
        df = pd.read_csv(csv_path, nrows=limit_rows)
        df.to_csv(csv_path, index=False)
        LOGGER.info("Trimmed ECOBICI trips to %s rows", limit_rows)

    return csv_path