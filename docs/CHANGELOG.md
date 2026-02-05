# Changelog

All notable changes to this project will be documented in this file.

---

## [0.1.0] - 2026-01-25 🚀

### Added - Core Features
- Interactive Streamlit dashboard with 7 tabs (Overview, Executive Brief, Map, GPS Proxy, Accessibility, Trends, Priority Index)
- GPS-proxy methodology using C5 incident data for mobility demand analysis
- Origin-Destination matrices with H3 hexagonal spatial indexing (resolution 9, ~180m)
- Accessibility analysis (stops density, proximity, travel time, isochrone buckets)
- Executive Brief with narrative, action board, and alert watch
- Priority/Policy Readiness Index (PPI) calculation

### Added - UI/UX Enhancements
- Professional dark Plotly theme applied to all 7 charts
- 7 CSV export buttons for data download
- Hero header with logo (🚦), version badge, and data freshness indicator
- Empty states with icons and helpful messages
- Loading spinners with custom messages
- Tooltips on KPI metrics cards
- Peak annotations on trend charts
- Responsive design with 3 breakpoints (desktop/tablet/mobile)

### Added - Development & Documentation
- CI/CD pipeline with GitHub Actions (Python 3.10, 3.11, 3.12)
- Complete documentation suite (ARCHITECTURE, CONTRIBUTING, QUICKREF, INDEX)
- MIT License for open source distribution
- Automated setup with Makefile (11 commands)
- Environment verification script (verify_setup.py)
- pyproject.toml for modern Python packaging

### Changed
- Migrated from requirements.txt to pyproject.toml
- Enhanced README with methodology explanation, badges, and use cases
- Improved docstrings in geo.py and ppi.py modules
- Custom CSS theme for professional dashboard appearance

### Fixed
- Cleaned up test artifacts (pytest-cache directories)
- Removed redundant documentation files (7 files → backup)
- Optimized .gitignore for data directories

### Technical Stack
- **Python**: 3.10+
- **Dashboard**: Streamlit 1.28+, Plotly 5.18+
- **Geospatial**: GeoPandas 0.14+, H3 3.7+
- **Validation**: Pandera 0.17+
- **Storage**: PyArrow 14.0+ (Parquet)
- **Testing**: pytest, GitHub Actions
- **Linting**: ruff, mypy

---

## Unreleased

### Planned
- GTFS real-time integration
- ECOBICI trip analytics enhancement
- Machine learning models for demand prediction
- Multi-city support
- API endpoints for data access
- Mobile app companion

---

**Format**: Based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
