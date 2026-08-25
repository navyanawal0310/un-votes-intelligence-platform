"""
Canonical analytical input layer.

All downstream analytical modules consume data
through this interface rather than reading raw
or Silver datasets directly.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "undl_id",
    "ms_code",
    "body_code",
    "vote_code",
    "vote_score",
    "date",
    "resolution",
    "year",
}


def load_analytical_input(
    path: Path,
) -> pd.DataFrame:
    """
    Load the canonical Gold analytical dataset.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Gold analytical dataset not found: {path}"
        )

    df = pd.read_parquet(path)

    missing = REQUIRED_COLUMNS - set(df.columns)

    if missing:
        raise ValueError(
            "Gold analytical dataset is missing "
            f"required columns: {sorted(missing)}"
        )

    df["ms_code"] = (
        df["ms_code"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df["body_code"] = (
        df["body_code"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df["vote_score"] = pd.to_numeric(
        df["vote_score"],
        errors="coerce",
    )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    return df


def validate_analytical_input(
    df: pd.DataFrame,
) -> None:
    """
    Validate invariants required by downstream analytics.

    Canonical UN vote-score representation:

        YES        = +1
        ABSTAIN    =  0
        NO         = -1
        NON-VOTING = NaN

    Missing vote scores are therefore valid and represent
    non-voting / unavailable position information.
    """

    if df.empty:
        raise ValueError(
            "Analytical input dataset is empty."
        )

    # Vote scores must be within the canonical
    # directional range [-1, +1].
    invalid_scores = df[
        df["vote_score"].notna()
        & ~df["vote_score"].between(-1, 1)
    ]

    if not invalid_scores.empty:
        raise ValueError(
            "vote_score contains values outside "
            "the canonical range [-1, 1]."
        )

    if df["ms_code"].isna().any():
        raise ValueError(
            "Analytical input contains missing country codes."
        )

    if df["year"].isna().any():
        raise ValueError(
            "Analytical input contains missing years."
        )