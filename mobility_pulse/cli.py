"""Command-line interface for mobility_pulse."""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

from mobility_pulse import config
from mobility_pulse.analytics.aggregates import build_analytics
from mobility_pulse.analytics.ppi import build_ppi
from mobility_pulse.ingest.c5 import ingest_c5
from mobility_pulse.ingest.ecobici_rt import ingest_ecobici_rt
from mobility_pulse.ingest.ecobici_trips import ingest_ecobici_trips
from mobility_pulse.ingest.gps_cdmx import ingest_gps_cdmx
from mobility_pulse.ingest.gtfs import ingest_gtfs
from mobility_pulse.logging_config import setup_logging
from mobility_pulse.transform.standardize import standardize_all
from mobility_pulse.validate.quality_report import generate_report

LOGGER = logging.getLogger(__name__)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="mobility_pulse")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest a data source")
    ingest_parser.add_argument(
        "--source",
        required=True,
        choices=["gtfs", "c5", "ecobici_rt", "ecobici_trips", "gps_cdmx"],
    )
    ingest_parser.add_argument("--snapshots", type=int, default=1)
    ingest_parser.add_argument("--interval_sec", type=int, default=300)
    ingest_parser.add_argument("--limit_rows", type=int, default=None)

    subparsers.add_parser("validate", help="Run data validation")
    subparsers.add_parser("build", help="Run transforms and analytics")
    subparsers.add_parser("app", help="Run Streamlit app")
    subparsers.add_parser("report", help="Generate PDF report")
    subparsers.add_parser("clean", help="Remove generated files")

    return parser.parse_args(argv)


def _run_app() -> None:
    app_path = Path(__file__).resolve().parent / "app" / "streamlit_app.py"
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
    raise SystemExit(subprocess.call(cmd))


def main(argv: list[str] | None = None) -> None:
    setup_logging()
    config.ensure_dirs()
    args = _parse_args(argv)

    if args.command == "ingest":
        if args.source == "gtfs":
            ingest_gtfs()
        elif args.source == "c5":
            ingest_c5()
        elif args.source == "ecobici_rt":
            ingest_ecobici_rt(snapshots=args.snapshots, interval_sec=args.interval_sec)
        elif args.source == "ecobici_trips":
            ingest_ecobici_trips(limit_rows=args.limit_rows)
        elif args.source == "gps_cdmx":
            ingest_gps_cdmx()
        else:
            raise SystemExit("Unknown source")
        return

    if args.command == "validate":
        generate_report()
        return

    if args.command == "build":
        standardize_all()
        build_analytics()
        build_ppi()
        return

    if args.command == "app":
        _run_app()
        return

    if args.command == "report":
        from mobility_pulse.reporting.pdf_report import generate_report_bundle

        generate_report_bundle()
        return

    if args.command == "clean":
        from mobility_pulse.clean import clean_generated

        clean_generated()
        return

    LOGGER.error("Unknown command")
