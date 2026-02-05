"""GTFS ingest logic."""

from __future__ import annotations

import logging
import zipfile
from pathlib import Path

import pandas as pd
import requests

from mobility_pulse.config import RAW_DIR, get_dataset_url

LOGGER = logging.getLogger(__name__)


def ingest_gtfs() -> Path:
    """Download and extract the GTFS feed."""
    url = get_dataset_url("gtfs")
    raw_dir = RAW_DIR / "gtfs"
    extract_dir = raw_dir / "extracted"
    raw_dir.mkdir(parents=True, exist_ok=True)
    extract_dir.mkdir(parents=True, exist_ok=True)

    zip_path = raw_dir / "gtfs.zip"
    LOGGER.info("Downloading GTFS from %s", url)
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with zip_path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)

    LOGGER.info("Extracting GTFS to %s", extract_dir)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)

    # Quick read to ensure files are present (optional)
    stops_path = extract_dir / "stops.txt"
    if stops_path.exists():
        _ = pd.read_csv(stops_path, nrows=5)
        LOGGER.info("Sampled stops.txt successfully")
    else:
        LOGGER.warning("stops.txt not found in GTFS archive")

    return zip_path