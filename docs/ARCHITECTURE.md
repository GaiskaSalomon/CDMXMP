# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CDMX Mobility Pulse                          │
│                    Reproducible Mobility Analytics Pipeline          │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│   INGEST     │  Download raw datasets from multiple sources
└──────┬───────┘
       │
       ├─► GTFS (static feed)        → data/raw/gtfs/
       ├─► C5 Incidents (CSV)        → data/raw/c5/
       ├─► ECOBICI RT (GBFS API)     → data/raw/ecobici/rt/
       ├─► ECOBICI Trips (monthly)   → data/raw/ecobici/trips/
       └─► GPS/CKAN (auto-discover)  → data/raw/gps/
       
       ↓

┌──────────────┐
│  VALIDATE    │  Schema validation & quality checks
└──────┬───────┘
       │
       └─► Pandera schemas → reports/data_quality.md
       
       ↓

┌──────────────┐
│  TRANSFORM   │  Standardize, geocode, add H3 zones
└──────┬───────┘
       │
       ├─► Standardize columns (timestamp, lat, lon, source)
       ├─► Add H3 hexagonal zones (resolution 9 ≈ 180m)
       ├─► GeoDataFrame conversions
       └─► Export Parquet → data/processed/
       
       ↓

┌──────────────┐
│  ANALYTICS   │  Aggregate & compute metrics
└──────┬───────┘
       │
       ├─► Temporal aggregations (hourly, daily, monthly)
       ├─► PPI (Priority/Policy Index): incidents + exposure
       ├─► Accessibility scores: transit coverage per zone
       └─► Export analytics → data/analytics/
       
       ↓

┌──────────────┐
│   VISUALIZE  │  Interactive dashboard & reports
└──────┬───────┘
       │
       ├─► Streamlit app (port 8501)
       │   ├─► Interactive maps (Plotly + H3 heatmaps)
       │   ├─► Executive brief (auto-generated insights)
       │   ├─► Temporal trends & filters
       │   └─► Accessibility analysis
       │
       └─► PDF/HTML reports → reports/
```

---

## Data Flow

```
Raw Data (CSV/JSON/ZIP)
    ↓ [Ingest Modules]
Parquet Files (data/raw/)
    ↓ [Schema Validation]
Quality Report (Markdown)
    ↓ [Standardization + Geo]
Processed Parquet (data/processed/)
    ↓ [Aggregation Modules]
Analytics Tables (data/analytics/)
    ↓ [Streamlit App]
Dashboard (Interactive)
    ↓ [Report Generator]
PDF/HTML Reports
```

---

## Key Design Decisions

### 1. **H3 Hexagonal Hierarchical Spatial Index**
- **Why**: Uniform area, hierarchical aggregation, multi-resolution
- **Resolution 9**: ~180m edge length (~0.1 km²)
- **Alternative considered**: Administrative boundaries (alcaldías, colonias)
- **Trade-off**: H3 is uniform but doesn't align with political boundaries

### 2. **Parquet for Intermediate Storage**
- **Why**: Columnar format, fast reads, compression, schema enforcement
- **Alternative**: CSV (human-readable but slower, no types)
- **Trade-off**: Requires PyArrow dependency

### 3. **Streamlit for Visualization**
- **Why**: Fast prototyping, Python-native, reactive UI
- **Alternative**: Dash/Flask (more control but more code)
- **Trade-off**: Limited customization, but rapid iteration

### 4. **Pandera for Validation**
- **Why**: Schema-as-code, auto-generated documentation
- **Alternative**: Manual checks, Pydantic
- **Trade-off**: Learning curve, but ensures data quality

### 5. **Makefile for Orchestration**
- **Why**: Simple, portable, explicit steps
- **Alternative**: Airflow/Prefect (more features but heavy)
- **Trade-off**: No scheduling, but lightweight

### 6. **Config-Driven URLs**
- **Why**: Easy updates when data sources change
- **File**: `config/datasets.yml`
- **Overrides**: Environment variables
- **Trade-off**: Extra indirection, but flexible

---

## Module Architecture

```
mobility_pulse/
├── __init__.py
├── cli.py              # Command-line interface (argparse)
├── config.py           # Paths, constants, config loading
├── logging_config.py   # Structured logging setup
│
├── ingest/             # Data acquisition modules
│   ├── gtfs.py         # GTFS static feed download + extract
│   ├── c5.py           # C5 incidents CSV download
│   ├── ecobici_rt.py   # GBFS real-time snapshots
│   ├── ecobici_trips.py# Monthly CSV download (with row limit)
│   └── gps_cdmx.py     # CKAN auto-discovery for GPS datasets
│
├── validate/           # Data quality checks
│   ├── schemas.py      # Pandera schema definitions
│   └── quality_report.py # Markdown report generator
│
├── transform/          # Data standardization
│   ├── standardize.py  # Column mapping, type conversion
│   └── geo.py          # H3 zoning, GeoDataFrame conversion
│
├── analytics/          # Metric computation
│   ├── aggregates.py   # Temporal aggregations, accessibility
│   └── ppi.py          # Priority/Policy Readiness Index
│
├── reporting/          # Output generation
│   └── pdf_report.py   # PDF/HTML/Markdown reports
│
└── app/                # Interactive dashboard
    └── streamlit_app.py # Multi-tab dashboard (1773 lines)
```

---

## Pipeline Stages

### Stage 1: Ingest
**Purpose**: Download raw data from external sources  
**Idempotency**: Re-running downloads overwrites existing files  
**Error handling**: HTTP errors logged, no retry logic (manual re-run)

### Stage 2: Validate
**Purpose**: Check data quality before processing  
**Outputs**: Markdown report with missingness, duplicates, out-of-bounds  
**Non-blocking**: Warnings only, does not halt pipeline

### Stage 3: Build
**Purpose**: Standardize schemas, add spatial zones, compute analytics  
**Key transformations**:
- Column renaming → consistent schema
- H3 zoning → `zone_id` column added
- Time parsing → `timestamp` column standardized
- Aggregations → hourly/daily/monthly tables

### Stage 4: Visualize
**Purpose**: Interactive exploration and executive reporting  
**Components**:
- Map tab: Point data + H3 heatmap mode
- Trends tab: Time-series charts with filters
- Accessibility tab: Transit coverage analysis
- Executive tab: Auto-generated insights + KPIs

---

## Scalability Considerations

### Current Limitations
- **In-memory processing**: Pandas/GeoPandas load full datasets
- **Single-threaded**: No parallel ingestion
- **Local storage**: No database backend
- **Manual execution**: No scheduling/orchestration

### Future Scaling Strategies
1. **Dask/Polars**: For datasets >1GB
2. **PostgreSQL + PostGIS**: Persistent storage + spatial queries
3. **Airflow/Prefect**: Scheduled pipeline runs
4. **DuckDB**: Fast analytics on Parquet without full loading
5. **Partitioned Parquet**: Date-based partitions for incremental updates

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Language | Python 3.10+ | Primary language |
| Data frames | Pandas, GeoPandas | Tabular + geospatial data |
| Spatial index | H3, Shapely | Hexagonal zoning, geometry |
| Storage | Parquet (PyArrow) | Columnar storage |
| Validation | Pandera | Schema enforcement |
| Visualization | Streamlit, Plotly | Interactive dashboard |
| Config | YAML, dotenv | Dataset URLs, settings |
| CLI | argparse | Command interface |
| Testing | pytest | Unit + integration tests |
| Linting | ruff | Code quality |

---

## Reproducibility

The pipeline is designed for full reproducibility:

1. **Config-driven**: All URLs in `config/datasets.yml`
2. **Environment isolation**: `requirements.txt` pins versions
3. **Makefile**: Single-command execution (`make data`)
4. **Documentation**: Inline docstrings + external docs
5. **Tests**: Synthetic data tests for CI/CD
6. **Logging**: Structured logs for debugging

---

## Extension Points

To adapt this pipeline to other cities:

1. **Update `config/datasets.yml`**:
   - Replace URLs with local data sources
   - Add new sources as needed

2. **Adjust H3 resolution** (`config.py`):
   - Lower resolution (7-8) for smaller cities
   - Higher resolution (10-11) for fine-grained analysis

3. **Customize schemas** (`validate/schemas.py`):
   - Adapt to local column names
   - Add validation rules

4. **Extend ingest modules** (`ingest/`):
   - Create new modules for local APIs
   - Follow existing patterns

5. **Modify dashboard** (`app/streamlit_app.py`):
   - Adjust KPIs for local context
   - Add tabs for local analysis

---

## Development Workflow

```bash
# Setup
make setup

# Data pipeline
make data      # Download raw data
make validate  # Check data quality
make build     # Process + compute analytics

# Development
make test      # Run pytest
make lint      # Format + check code

# Visualization
make app       # Launch Streamlit dashboard
make report    # Generate PDF/HTML reports
```

---

## Security & Privacy Considerations

- **No credentials in code**: Use environment variables
- **Public data only**: All sources are open data
- **No PII**: Aggregate spatial zones (no individual tracking)
- **Data retention**: Raw data in gitignore, not committed

---

## Performance Metrics (Typical Run)

| Stage | Dataset Size | Processing Time |
|-------|-------------|-----------------|
| Ingest GTFS | ~15 MB (zipped) | 5-10s |
| Ingest C5 | ~500K rows | 15-30s |
| Ingest ECOBICI | ~100K rows | 10-20s |
| Validate | All datasets | 5-10s |
| Build | All datasets | 30-60s |
| App startup | - | 3-5s |

**Total pipeline**: ~2-3 minutes (with 100K trip limit)

---

## References

- [H3 Spatial Index](https://h3geo.org/)
- [GTFS Specification](https://gtfs.org/)
- [GBFS Specification](https://github.com/MobilityData/gbfs)
- [Pandera Documentation](https://pandera.readthedocs.io/)
- [Streamlit Documentation](https://docs.streamlit.io/)
