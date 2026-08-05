"""
Data models used by the dataset profiler.
"""

from dataclasses import dataclass

import pandas as pd


@dataclass(slots=True)
class DatasetProfile:
    """
    Stores the profiling results for a dataset.
    """

    rows: int
    columns: int

    metadata_columns: list[str]
    country_columns: list[str]

    duplicate_rows: int
    memory_usage_mb: float

    missing_values: pd.Series
    dtypes: pd.Series