# Contributing to CDMX Mobility Pulse

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

---

## 🎯 Ways to Contribute

- **Report bugs** by opening an issue
- **Suggest features** or improvements
- **Add support for other cities** (configs, data sources)
- **Improve documentation** (typos, clarifications, translations)
- **Write tests** for uncovered code
- **Submit code improvements** (bug fixes, refactoring, new features)

---

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/CDMXMP.git
cd CDMXMP
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install in development mode
make setup

# Or manually:
pip install -e .[dev]
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

---

## 💻 Development Workflow

### Running Tests

```bash
make test           # Run all tests
pytest -v           # Verbose output
pytest tests/test_smoke_pipeline.py  # Specific test file
```

### Code Quality

```bash
make lint           # Format and check code
ruff check .        # Check for issues
ruff format .       # Auto-format code
```

### Running the Pipeline Locally

```bash
make data           # Download and process data
make validate       # Generate quality report
make build          # Build analytics tables
make app            # Launch dashboard
```

---

## 📝 Code Style Guidelines

### General Principles
- **Follow PEP 8** (enforced by ruff)
- **Use type hints** for function signatures
- **Write docstrings** for public functions (Google style)
- **Keep functions focused** (single responsibility)
- **Prefer explicit over implicit**

### Example Function

```python
def add_zone_id(
    df: pd.DataFrame,
    lat_col: str = "lat",
    lon_col: str = "lon",
    resolution: int | None = None,
) -> pd.DataFrame:
    """Assign H3 zone_id to rows with valid lat/lon.
    
    Args:
        df: Input DataFrame with latitude/longitude columns.
        lat_col: Name of latitude column (default: "lat").
        lon_col: Name of longitude column (default: "lon").
        resolution: H3 resolution level 0-15 (default: config.DEFAULT_H3_RESOLUTION).
    
    Returns:
        DataFrame with added 'zone_id' column (H3 cell string).
        Rows with invalid coordinates get None for zone_id.
    
    Example:
        >>> df = pd.DataFrame({"lat": [19.43], "lon": [-99.13]})
        >>> df = add_zone_id(df)
        >>> df["zone_id"].iloc[0]
        '89283082833ffff'
    """
    # Implementation...
```

### Naming Conventions
- **Functions/variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private helpers**: `_leading_underscore`

### Import Order
1. Standard library
2. Third-party packages
3. Local modules

```python
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import geopandas as gpd

from mobility_pulse.config import PROCESSED_DIR
```

---

## 🧪 Writing Tests

### Test Structure

```python
def test_feature_name(tmp_path: Path, monkeypatch) -> None:
    """Test description: what scenario and expected outcome."""
    # Arrange: set up test data
    input_df = pd.DataFrame({"col": [1, 2, 3]})
    
    # Act: call function under test
    result = my_function(input_df)
    
    # Assert: verify expected behavior
    assert len(result) == 3
    assert "new_col" in result.columns
```

### What to Test
- ✅ **Happy path**: normal inputs produce expected outputs
- ✅ **Edge cases**: empty data, missing columns, null values
- ✅ **Error handling**: invalid inputs raise appropriate errors
- ❌ **Don't test external APIs** (use mocks or fixtures)

### Running Specific Tests

```bash
pytest tests/test_smoke_pipeline.py::test_build_analytics_and_ppi -v
pytest -k "test_analytics" -v  # All tests matching pattern
```

---

## 🌍 Adding Support for New Cities

### 1. Create Config File

Add entry to [`config/datasets.yml`](config/datasets.yml):

```yaml
guadalajara:
  gtfs:
    url: "https://example.com/guadalajara-gtfs.zip"
  incidents:
    url: "https://datos.guadalajara.gob.mx/incidents.csv"
```

### 2. Test with Sample Data

```bash
MOBILITY_PULSE_GTFS_URL="https://your-url.zip" make data
```

### 3. Document City-Specific Notes

Create `docs/cities/guadalajara.md` with:
- Data source details
- Update frequency
- Known issues or quirks
- Contact information

### 4. Submit Pull Request

Include:
- Config changes
- Sample data (if small) or download instructions
- Documentation updates
- Test verification (screenshots or logs)

---

## 📚 Documentation Standards

### README Updates
- Keep examples **concise and runnable**
- Update screenshots if UI changes
- Test all code snippets before committing

### Docstrings
- **Module-level**: Brief description at top of file
- **Function-level**: Args, Returns, Raises, Example
- **Class-level**: Purpose, attributes, usage example

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add support for Monterrey GTFS data
fix: handle missing timestamps in C5 incidents
docs: update installation instructions for Windows
test: add coverage for H3 edge cases
refactor: simplify accessibility calculation
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Add or update tests
- `refactor`: Code restructuring (no behavior change)
- `perf`: Performance improvement
- `chore`: Maintenance (dependencies, config)

---

## 🔍 Pull Request Process

### Before Submitting

1. **Run tests**: `make test` passes
2. **Check linting**: `make lint` passes
3. **Update docs**: If adding features
4. **Add tests**: For new functionality
5. **Rebase**: On latest `main` branch

```bash
git fetch upstream
git rebase upstream/main
```

### PR Template

```markdown
## Description
Brief summary of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Tests pass locally
- [ ] Added new tests (if applicable)
- [ ] Linting passes

## Screenshots (if UI changes)
[Attach before/after images]

## Related Issues
Closes #123
```

### Review Process

1. **Automated checks** must pass (CI)
2. **Code review** by maintainer
3. **Requested changes** addressed
4. **Merge** when approved

---

## 🐛 Reporting Bugs

### Good Bug Reports Include:

1. **Clear title**: "C5 ingest fails with HTTP 404"
2. **Steps to reproduce**:
   ```bash
   make setup
   make data
   # Error appears here
   ```
3. **Expected behavior**: "Should download incidents CSV"
4. **Actual behavior**: "HTTP 404 error"
5. **Environment**:
   - OS: Windows 11
   - Python: 3.11.5
   - Package version: 0.1.0
6. **Logs/screenshots**: Copy error traceback

### Use Issue Templates

The repository provides templates for:
- 🐛 Bug reports
- ✨ Feature requests
- 📖 Documentation improvements

---

## 💡 Feature Requests

Good feature requests:
- **Explain the problem**: What limitation exists today?
- **Describe the solution**: What would you like to see?
- **Consider alternatives**: Are there other approaches?
- **Provide context**: Who benefits and why?

Example:
> **Problem**: Manual entry of alcaldía boundaries is tedious.
> 
> **Solution**: Add automatic download from INEGI API.
> 
> **Alternative**: Accept GeoJSON upload in dashboard.
> 
> **Benefit**: Reduces setup time for new users, improves accuracy.

---

## 🎨 Code of Conduct

### Our Standards

- ✅ Be respectful and inclusive
- ✅ Welcome diverse perspectives
- ✅ Accept constructive criticism gracefully
- ✅ Focus on what's best for the community
- ❌ No harassment, trolling, or personal attacks

### Enforcement

Violations can be reported to project maintainers. All reports are confidential.

---

## 📧 Questions?

- **General questions**: Open a Discussion on GitHub
- **Bug reports**: Open an Issue
- **Security issues**: Email maintainers directly (see README)
- **Pull requests**: Follow PR process above

---

## 🙏 Recognition

Contributors are recognized in:
- **README.md** acknowledgments section
- **Release notes** for their contributions
- **Git history** (commits properly attributed)

---

**Thank you for contributing to sustainable urban mobility!** 🚴‍♀️🚌🚶‍♂️
