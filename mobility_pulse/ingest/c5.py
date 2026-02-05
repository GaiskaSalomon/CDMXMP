"""C5 incidents ingest logic."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import requests

from mobility_pulse.config import RAW_DIR, get_dataset_url

LOGGER = logging.getLogger(__name__)


def ingest_c5() -> Path:
    """Download C5 incidents CSV."""
    url = get_dataset_url("c5")
    raw_dir = RAW_DIR / "c5"
    raw_dir.mkdir(parents=True, exist_ok=True)

    csv_path = raw_dir / "c5_incidents.csv"
    LOGGER.info("Downloading C5 incidents from %s", url)
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with csv_path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)

    try:
        _ = pd.read_csv(csv_path, nrows=5)
        LOGGER.info("Sampled C5 CSV successfully")
    except Exception as exc:
        LOGGER.warning("Could not read C5 CSV sample: %s", exc)

    return csv_path