# Pipeline overview

## Stages
1. Ingest: downloads raw datasets into `data/raw/`.
2. Validate: runs schema checks and creates `reports/data_quality.md`.
3. Build: standardizes data, adds H3 zones, and generates analytics tables.
4. App: Streamlit dashboard for exploration and executive reporting.

## Outputs
- `data/processed/*.parquet` standardized datasets
- `data/analytics/*.parquet` aggregated tables used by the app
