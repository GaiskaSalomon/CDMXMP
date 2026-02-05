"""ECOBICI real-time (GBFS) ingest logic."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from mobility_pulse.config import RAW_DIR, get_dataset_url

LOGGER = logging.getLogger(__name__)


def _fetch_json(url: str) -> dict[str, Any]:
    with requests.get(url, timeout=30) as response:
        response.raise_for_status()
        return response.json()


def _resolve_gbfs_links(payload: dict[str, Any]) -> dict[str, str]:
    data = payload.get("data", {})
    # Prefer "es" or "en" language keys
    for lang in ("es", "en"):
        if lang in data:
            feeds = data[lang].get("feeds", [])
            return {item["name"]: item["url"] for item in feeds if "url" in item}
    # Fallback: take first language
    if data:
        first_lang = next(iter(data))
        feeds = data[first_lang].get("feeds", [])
        return {item["name"]: item["url"] for item in feeds if "url" in item}
    return {}


def ingest_ecobici_rt(snapshots: int = 1, interval_sec: int = 300) -> Path:
    """Fetch GBFS station info/status and save snapshots."""
    url = get_dataset_url("ecobici_rt")
    raw_dir = RAW_DIR / "ecobici" / "rt"
    json_dir = raw_dir / "json"
    parsed_dir = raw_dir / "parsed"
    json_dir.mkdir(parents=True, exist_ok=True)
    parsed_dir.mkdir(parents=True, exist_ok=True)

    all_snapshots: list[pd.DataFrame] = []

    for idx in range(snapshots):
        LOGGER.info("Fetching ECOBICI GBFS root from %s", url)
        root = _fetch_json(url)
        timestamp = datetime.now().astimezone().isoformat()
        root_path = json_dir / f"gbfs_root_{idx + 1}.json"
        root_path.write_text(json.dumps(root, indent=2), encoding="utf-8")

        feeds = _resolve_gbfs_links(root)
        station_info_url = feeds.get("station_information")
        station_status_url = feeds.get("station_status")
        if not station_info_url or not station_status_url:
            raise RuntimeError(
                "GBFS feed missing station_information or station_status"
            )

        station_info = _fetch_json(station_info_url)
        station_status = _fetch_json(station_status_url)

        (json_dir / f"station_information_{idx + 1}.json").write_text(
            json.dumps(station_info, indent=2),
            encoding="utf-8",
        )
        (json_dir / f"station_status_{idx + 1}.json").write_text(
            json.dumps(station_status, indent=2),
            encoding="utf-8",
        )

        info_df = pd.DataFrame(station_info.get("data", {}).get("stations", []))
        status_df = pd.DataFrame(station_status.get("data", {}).get("stations", []))

        snapshot_df = info_df.merge(status_df, on="station_id", how="left")
        snapshot_df["timestamp"] = timestamp
        snapshot_df["source"] = "ecobici_rt"
        all_snapshots.append(snapshot_df)

        if idx < snapshots - 1:
            time.sleep(interval_sec)

    out_path = parsed_dir / "station_snapshots.parquet"
    if all_snapshots:
        pd.concat(all_snapshots, ignore_index=True).to_parquet(out_path, index=False)
        LOGGER.info("Saved %s", out_path)

    return out_path
