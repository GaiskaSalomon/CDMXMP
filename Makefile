.PHONY: help setup data validate build app report test lint clean check

help:
	@echo "CDMX Mobility Pulse - Available Commands"
	@echo "========================================"
	@echo "  make setup      Install dependencies"
	@echo "  make data       Download & process all datasets"
	@echo "  make validate   Generate data quality report"
	@echo "  make build      Build analytics tables"
	@echo "  make app        Launch Streamlit dashboard"
	@echo "  make report     Generate PDF/HTML reports"
	@echo "  make test       Run pytest tests"
	@echo "  make lint       Format & check code with ruff"
	@echo "  make clean      Remove generated files"
	@echo "  make check      Run tests + linting (pre-commit)"
	@echo ""
	@echo "Quick Start: make setup && make data && make app"

setup:
	python -m pip install -e .[dev]

data:
	python -m mobility_pulse ingest --source gtfs
	python -m mobility_pulse ingest --source c5
	python -m mobility_pulse ingest --source ecobici_rt --snapshots 1
	python -m mobility_pulse ingest --source ecobici_trips --limit_rows 100000
	python -m mobility_pulse ingest --source gps_cdmx

validate:
	python -m mobility_pulse validate

build:
	python -m mobility_pulse build

app:
	python -m mobility_pulse app

report:
	python -m mobility_pulse report

test:
	pytest -v

lint:
	ruff check .
	ruff format .

clean:
	python -m mobility_pulse clean

check: test lint
	@echo "✅ All checks passed!"
