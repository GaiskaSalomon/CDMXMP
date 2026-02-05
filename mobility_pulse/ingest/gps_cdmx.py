"""GPS ingest via CDMX CKAN search."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests

from mobility_pulse.config import RAW_DIR, get_dataset_url, load_datasets

LOGGER = logging.getLogger(__name__)


def _search_ckan(base_url: str, keywords: list[str], rows: int = 50) -> dict[str, Any]:
    query = " OR ".join([f'"{kw}"' for kw in keywords])
    params = {"q": query, "rows": rows}
    with requests.get(base_url, params=params, timeout=30) as response:
        response.raise_for_status()
        return response.json()


def _pick_resource(results: list[dict[str, Any]]) -> dict[str, Any] | None:
    for dataset in results:
        resources = dataset.get("resources") or []
        for res in resources:
            url = res.get("url")
            fmt = str(res.get("format", "")).lower()
            if url and fmt in {"csv", "geojson", "json"}:
                return {
                    "dataset": dataset.get("name"),
                    "title": dataset.get("title"),
                    "resource": res,
                }
    return None


def ingest_gps_cdmx() -> Path:
    """Search CDMX CKAN for GPS-like datasets and download a candidate resource."""
    datasets = load_datasets()
    base_url = get_dataset_url("gps_cdmx", datasets=datasets)
    cfg = datasets.get("gps_cdmx")
    keyword_list = []
    if cfg:
        if cfg.keywords:
            keyword_list = cfg.keywords
        elif isinstance(cfg.description, list):
            keyword_list = cfg.description
    if not keyword_list:
        keyword_list = [
            "gps",
            "geolocalizacion",
            "trayectos",
            "recorridos",
            "movilidad",
        ]

    raw_dir = RAW_DIR / "gps"
    raw_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Searching CKAN for GPS datasets: %s", keyword_list)
    payload = _search_ckan(base_url, keyword_list)
    (raw_dir / "ckan_search.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    results = payload.get("result", {}).get("results", [])
    pick = _pick_resource(results)
    if not pick:
        notice = raw_dir / "no_gps_dataset_found.txt"
        notice.write_text(
            "No GPS-like dataset found via CKAN search. Check ckan_search.json and update keywords or select manually.",
            encoding="utf-8",
        )
        LOGGER.warning("No GPS dataset found. See %s", notice)
        return notice

    resource = pick["resource"]
    url = resource.get("url")
    fmt = str(resource.get("format", "")).lower()
    filename = (
        f"gps_cdmx.{fmt}" if fmt in {"csv", "geojson", "json"} else "gps_cdmx.data"
    )
    out_path = raw_dir / filename

    LOGGER.info("Downloading GPS candidate: %s", url)
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with out_path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)

    meta_path = raw_dir / "gps_cdmx_metadata.json"
    meta_path.write_text(json.dumps(pick, indent=2), encoding="utf-8")
    LOGGER.info("Saved GPS dataset to %s", out_path)
    return out_path
