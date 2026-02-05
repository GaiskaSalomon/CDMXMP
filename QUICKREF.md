# Quick Reference

## Installation & Setup

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/CDMXMP.git
cd CDMXMP

# Setup (one time)
make setup
```

## Pipeline Commands

```bash
make data       # Download all datasets (~2-3 min)
make validate   # Check data quality
make build      # Generate analytics
make app        # Launch dashboard
```

## Development

```bash
make test       # Run tests
make lint       # Format & check code
make check      # Run both tests + linting
make clean      # Remove generated files
make help       # Show all commands
```

## Project Structure

```
CDMXMP/
├── mobility_pulse/         # Main package
│   ├── ingest/            # Data download modules
│   ├── validate/          # Schema validation
│   ├── transform/         # H3 zoning, standardization
│   ├── analytics/         # PPI, aggregations, accessibility
│   ├── app/               # Streamlit dashboard
│   └── reporting/         # PDF/HTML reports
├── data/                  # Data directory (gitignored)
│   ├── raw/              # Downloaded datasets
│   ├── processed/        # Standardized parquet files
│   └── analytics/        # Aggregated tables
├── config/               # Configuration files
│   └── datasets.yml      # Data source URLs
├── docs/                 # Documentation
│   ├── ARCHITECTURE.md   # System design
│   ├── PIPELINE.md       # Pipeline overview
│   └── screenshots/      # Dashboard images
├── tests/                # Test files
├── reports/              # Generated reports
└── Makefile             # Automation commands
```

## Key Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview, quickstart |
| `CONTRIBUTING.md` | Contribution guidelines |
| `ARCHITECTURE.md` | Technical design decisions |
| `pyproject.toml` | Package metadata & dependencies |
| `config/datasets.yml` | Data source URLs |

## Common Tasks

### Update Data Sources
Edit `config/datasets.yml` or set environment variables:
```bash
export MOBILITY_PULSE_GTFS_URL="https://new-url.zip"
make data
```

### Change H3 Resolution
Edit `mobility_pulse/config.py`:
```python
DEFAULT_H3_RESOLUTION = 9  # 8=larger hexagons, 10=smaller
```

### Add New City
1. Add config to `datasets.yml`
2. Test: `make data`
3. Document in `docs/cities/YOUR_CITY.md`
4. Submit PR!

## Dashboard Tabs

| Tab | Description |
|-----|-------------|
| **Overview** | KPIs, data summary, peak patterns |
| **Executive Brief** | Auto-generated insights & actions |
| **Map** | Interactive points + H3 heatmap |
| **GPS Proxy** | Auto-discovered datasets via CKAN |
| **Accessibility** | Transit coverage analysis |
| **Trends** | Time-series with filters |
| **Priority Index** | PPI scores by zone |

## Troubleshooting

### "No module named mobility_pulse"
```bash
pip install -e .[dev]
```

### "File not found" errors
```bash
make data  # Download datasets first
```

### Tests failing
```bash
make clean  # Remove old data
make setup  # Reinstall dependencies
make test   # Re-run tests
```

### Dashboard won't start
```bash
# Check if port 8501 is in use
lsof -ti:8501 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8501   # Windows

# Try again
make app
```

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `MOBILITY_PULSE_GTFS_URL` | See config | GTFS feed URL |
| `MOBILITY_PULSE_C5_URL` | See config | C5 incidents URL |
| `MOBILITY_PULSE_ECOBICI_URL` | See config | ECOBICI GBFS URL |

## Performance Tips

- **Limit ECOBICI trips**: Use `--limit_rows 50000` for faster testing
- **Skip GPS ingest**: Comment out in Makefile if not needed
- **Use Parquet**: Already optimized, don't convert to CSV
- **H3 resolution**: Lower = faster (but coarser zones)

## Links

- 📖 [Full Documentation](README.md)
- 🏗️ [Architecture Guide](docs/ARCHITECTURE.md)
- 🤝 [Contributing](CONTRIBUTING.md)
- 🐛 [Report Issues](https://github.com/YOUR_USERNAME/CDMXMP/issues)
- 💬 [Discussions](https://github.com/YOUR_USERNAME/CDMXMP/discussions)

---

**Last Updated**: January 2026  
**Version**: 0.1.0
