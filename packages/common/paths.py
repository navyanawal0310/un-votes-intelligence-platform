"""
Centralized project paths.

Every module should import paths from this file instead of
hardcoding filesystem locations.
"""

from pathlib import Path

# ---------------------------------------------------------------------
# Project Root
# ---------------------------------------------------------------------

# packages/common/paths.py
# parents[2] -> project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------
# Data Directories
# ---------------------------------------------------------------------

DATA_DIR = PROJECT_ROOT / "data"

RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
WAREHOUSE_DATA_DIR = DATA_DIR / "warehouse"
ANALYTICS_DATA_DIR = DATA_DIR / "analytics"

DOWNLOADS_DIR = RAW_DATA_DIR / "downloads"

# ---------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------

REPORTS_DIR = PROJECT_ROOT / "reports"
PROFILING_REPORT_DIR = REPORTS_DIR / "profiling"

# ---------------------------------------------------------------------
# Documentation
# ---------------------------------------------------------------------

DOCS_DIR = PROJECT_ROOT / "docs"

# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

TESTS_DIR = PROJECT_ROOT / "tests"

# ---------------------------------------------------------------------
# Infrastructure
# ---------------------------------------------------------------------

INFRASTRUCTURE_DIR = PROJECT_ROOT / "infrastructure"

# ---------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------


def create_project_directories() -> None:
    """
    Create all project directories required by the pipeline.

    Existing directories are ignored.
    """

    directories = [
        DATA_DIR,
        RAW_DATA_DIR,
        DOWNLOADS_DIR,
        PROCESSED_DATA_DIR,
        WAREHOUSE_DATA_DIR,
        ANALYTICS_DATA_DIR,
        REPORTS_DIR,
        PROFILING_REPORT_DIR,
        DOCS_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)