"""CDMX Mobility Pulse package."""

import os

os.environ.setdefault("DISABLE_PANDERA_IMPORT_WARNING", "True")

from mobility_pulse.cli import main

__all__ = ["main"]
