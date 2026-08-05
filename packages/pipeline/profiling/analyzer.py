"""
Dataset profiling logic.
"""

from pathlib import Path

import pandas as pd

from .models import DatasetProfile

from packages.common.constants import METADATA_COLUMNS

def load_dataset(path: Path) -> pd.DataFrame:
    """
    Load the raw UN voting dataset.
    """
    return pd.read_csv(
        path,
        low_memory=False,
    )


def get_country_columns(df: pd.DataFrame) -> list[str]:
    """
    Return all country columns.
    """
    return [c for c in df.columns if c not in METADATA_COLUMNS]


def profile_dataset(df: pd.DataFrame) -> DatasetProfile:
    """
    Generate a dataset profile.
    """

    rows, columns = df.shape

    return DatasetProfile(
        rows=rows,
        columns=columns,
        metadata_columns=METADATA_COLUMNS,
        country_columns=get_country_columns(df),
        duplicate_rows=df.duplicated().sum(),
        memory_usage_mb=df.memory_usage(deep=True).sum() / 1024**2,
        missing_values=df.isna().sum(),
        dtypes=df.dtypes,
    )