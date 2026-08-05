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
    Generate a complete profile for the dataset.
    """

    rows, columns = df.shape

    country_columns = get_country_columns(df)

    duplicate_rows = int(df.duplicated().sum())

    memory_usage_mb = df.memory_usage(deep=True).sum() / (1024 ** 2)

    missing_values = df.isna().sum()

    dtypes = df.dtypes

    unique_vote_values = get_unique_vote_values(
        df,
        country_columns,
    )

    return DatasetProfile(
        rows=rows,
        columns=columns,
        metadata_columns=METADATA_COLUMNS,
        country_columns=country_columns,
        duplicate_rows=duplicate_rows,
        memory_usage_mb=memory_usage_mb,
        missing_values=missing_values,
        dtypes=dtypes,
        unique_vote_values=unique_vote_values,
    )
def get_unique_vote_values(
    df: pd.DataFrame,
    country_columns: list[str],
) -> list[str]:
    """
    Return all unique vote values found in the dataset.
    """

    values = set()

    for column in country_columns:
        column_values = (
            df[column]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
        )

        values.update(column_values)

    return sorted(values)