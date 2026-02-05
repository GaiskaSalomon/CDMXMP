"""Configuration helpers for dataset endpoints and paths."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "config" / "datasets.yml"
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
ANALYTICS_DIR = DATA_DIR / "analytics"
REPORTS_DIR = ROOT_DIR / "reports"

CDMX_BBOX = {
    "min_lon": -99.364,
    "min_lat": 19.048,
    "max_lon": -98.940,
    "max_lat": 19.592,
}

DEFAULT_H3_RESOLUTION = 9
DEFAULT_TIMEZONE = "America/Mexico_City"

# Silence pandera deprecation warning noise in CLI/app output.
os.environ.setdefault("DISABLE_PANDERA_IMPORT_WARNING", "True")


@dataclass(frozen=True)
class DatasetConfig:
    name: str
    url: str
    description: str | list[str] | None = None
    keywords: list[str] | None = None


class ConfigError(RuntimeError):
    """Configuration loading error."""


def load_datasets(path: Path | None = None) -> dict[str, DatasetConfig]:
    """Load datasets from YAML and apply environment overrides."""
    config_path = path or CONFIG_PATH
    if not config_path.exists():
        raise ConfigError(f"Missing config file: {config_path}")

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    datasets: dict[str, DatasetConfig] = {}
    for name, payload in raw.items():
        url = str(payload.get("url", "")).strip()
        env_key = f"MOBILITY_PULSE_{name.upper()}_URL"
        url = os.getenv(env_key, url)
        keywords = payload.get("keywords")
        if keywords is not None and not isinstance(keywords, list):
            keywords = [str(keywords)]
        datasets[name] = DatasetConfig(
            name=name,
            url=url,
            description=payload.get("description"),
            keywords=keywords,
        )
    return datasets


def get_dataset_url(name: str, datasets: dict[str, DatasetConfig] | None = None) -> str:
    """Get dataset URL by name, with env override applied."""
    datasets = datasets or load_datasets()
    if name not in datasets:
        raise ConfigError(f"Dataset '{name}' not defined in {CONFIG_PATH}")
    url = datasets[name].url
    if not url:
        raise ConfigError(f"Dataset '{name}' has no URL configured")
    return url


def ensure_dirs() -> None:
    """Ensure base data directories exist."""
    for path in (RAW_DIR, PROCESSED_DIR, ANALYTICS_DIR, REPORTS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def config_summary() -> dict[str, Any]:
    """Return a summary of key config values."""
    return {
        "root_dir": str(ROOT_DIR),
        "raw_dir": str(RAW_DIR),
        "processed_dir": str(PROCESSED_DIR),
        "analytics_dir": str(ANALYTICS_DIR),
        "reports_dir": str(REPORTS_DIR),
        "h3_resolution": DEFAULT_H3_RESOLUTION,
        "timezone": DEFAULT_TIMEZONE,
        "bbox": CDMX_BBOX,
    }
