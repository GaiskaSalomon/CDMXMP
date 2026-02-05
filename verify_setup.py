#!/usr/bin/env python3
"""Setup verification script for CDMX Mobility Pulse.

Run this after `make setup` to verify your environment is correctly configured.
"""

from __future__ import annotations

import sys
from pathlib import Path


def check_python_version() -> bool:
    """Check if Python version is 3.10+."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(
            f"❌ Python {version.major}.{version.minor} detected. Requires Python 3.10+"
        )
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_imports() -> bool:
    """Check if all required packages can be imported."""
    required = [
        ("pandas", "pandas"),
        ("geopandas", "geopandas"),
        ("h3", "h3"),
        ("streamlit", "streamlit"),
        ("plotly", "plotly"),
        ("sklearn", "scikit-learn"),
        ("xgboost", "xgboost"),
        ("lightgbm", "lightgbm"),
        ("catboost", "catboost"),
        ("statsmodels", "statsmodels"),
        ("pandera", "pandera"),
        ("yaml", "pyyaml"),
        ("pytest", "pytest"),
        ("ruff", "ruff"),
    ]

    all_ok = True
    for module, package in required:
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} not installed")
            all_ok = False

    return all_ok


def check_directories() -> bool:
    """Check if expected directories exist."""
    dirs = [
        "mobility_pulse",
        "config",
        "data",
        "docs",
        "tests",
    ]

    all_ok = True
    for d in dirs:
        path = Path(d)
        if path.exists():
            print(f"✅ {d}/")
        else:
            print(f"❌ {d}/ not found")
            all_ok = False

    return all_ok


def check_config_files() -> bool:
    """Check if configuration files exist."""
    files = [
        "config/datasets.yml",
        "pyproject.toml",
        "Makefile",
        "README.md",
    ]

    all_ok = True
    for f in files:
        path = Path(f)
        if path.exists():
            print(f"✅ {f}")
        else:
            print(f"❌ {f} not found")
            all_ok = False

    return all_ok


def main() -> int:
    """Run all verification checks."""
    print("=" * 60)
    print("CDMX Mobility Pulse - Setup Verification")
    print("=" * 60)

    print("\n📦 Checking Python version...")
    py_ok = check_python_version()

    print("\n📚 Checking package imports...")
    imports_ok = check_imports()

    print("\n📁 Checking directories...")
    dirs_ok = check_directories()

    print("\n⚙️  Checking configuration files...")
    config_ok = check_config_files()

    print("\n" + "=" * 60)

    if all([py_ok, imports_ok, dirs_ok, config_ok]):
        print("✅ All checks passed! You're ready to go.")
        print("\nNext steps:")
        print("  make data    # Download datasets")
        print("  make app     # Launch dashboard")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\nTroubleshooting:")
        print("  make setup   # Reinstall dependencies")
        print("  pip install -e .[dev]  # Manual installation")
        return 1


if __name__ == "__main__":
    sys.exit(main())
