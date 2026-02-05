"""Logging configuration."""

import logging


def setup_logging(level: int = logging.INFO) -> None:
    """Configure a simple logging format for CLI and modules."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )