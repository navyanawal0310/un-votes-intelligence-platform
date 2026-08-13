"""
Project-wide constants.

Only values that are unlikely to change frequently should live here.
Avoid placing configuration or environment-specific values in this file.
"""

# ============================================================================
# Dataset
# ============================================================================

DATASET_FILENAME = "2026_02_06_ga_voting.csv"

# ============================================================================
# Metadata Columns
# ============================================================================

METADATA_COLUMNS: list[str] = [
    "Council",
    "Date",
    "Title",
    "Resolution",
    "TOTAL VOTES",
    "NO-VOTE COUNT",
    "ABSENT COUNT",
    "NO COUNT",
    "YES COUNT",
    "Link",
    "token",
]

# ============================================================================
# Profiling Output Files
# ============================================================================

PROFILE_REPORT_FILENAME = "data_profile.md"

COUNTRY_COLUMNS_FILENAME = "country_columns.csv"

METADATA_COLUMNS_FILENAME = "metadata_columns.csv"

UNIQUE_VOTE_VALUES_FILENAME = "unique_vote_values.csv"

# ============================================================================
# Vote Categories
# ============================================================================

# We will validate against these later.
# Keep them here so validation logic doesn't hardcode values.

KNOWN_VOTE_VALUES = {
    "YES",
    "NO",
    "ABSTAIN",
    "ABSENT",
    "NO VOTE",
}

# ============================================================================
# Encoding
# ============================================================================

DEFAULT_ENCODING = "utf-8"

# ============================================================================
# CSV
# ============================================================================

CSV_SEPARATOR = ","