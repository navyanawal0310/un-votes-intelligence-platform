from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_gold(
    df: pd.DataFrame,
    output_path: Path,
) -> Path:
    """
    Persist an analytical dataset to the Gold layer.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "Gold output must be a pandas DataFrame."
        )

    if df.empty:
        raise ValueError(
            "Cannot write an empty Gold dataset."
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_parquet(
        output_path,
        index=False,
    )

    return output_path


def read_gold(
    path: Path,
) -> pd.DataFrame:
    """
    Load a Gold analytical dataset.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Gold dataset not found: {path}"
        )

    return pd.read_parquet(path)