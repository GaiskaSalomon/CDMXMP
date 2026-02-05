"""Project cleanup utilities."""

from __future__ import annotations

from pathlib import Path
import shutil

from mobility_pulse.config import (
    ANALYTICS_DIR,
    PROCESSED_DIR,
    RAW_DIR,
    REPORTS_DIR,
    ROOT_DIR,
)


def _remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    elif path.exists():
        path.unlink(missing_ok=True)


def _clear_dir_contents(path: Path) -> None:
    if not path.exists():
        return
    for item in path.iterdir():
        _remove_path(item)


def clean_generated() -> None:
    """Remove generated data, reports, and build artifacts."""
    _clear_dir_contents(RAW_DIR)
    _clear_dir_contents(PROCESSED_DIR)
    _clear_dir_contents(ANALYTICS_DIR)

    if REPORTS_DIR.exists():
        for item in REPORTS_DIR.iterdir():
            if item.is_dir() and item.name == "assets":
                _remove_path(item)
            elif item.suffix.lower() in {".html", ".pdf"}:
                _remove_path(item)

    for pattern in ("*.egg-info", "build", "dist"):
        for item in ROOT_DIR.glob(pattern):
            _remove_path(item)

    for cache_dir in ROOT_DIR.rglob("__pycache__"):
        _remove_path(cache_dir)
    for cache_dir in ROOT_DIR.rglob(".pytest_cache"):
        _remove_path(cache_dir)
    for pyc in ROOT_DIR.rglob("*.pyc"):
        _remove_path(pyc)

    print("Clean complete!")
