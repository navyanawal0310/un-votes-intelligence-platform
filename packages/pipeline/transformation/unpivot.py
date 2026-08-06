"""
Wide-to-long transformation for the UN voting dataset.
"""

from __future__ import annotations

import pandas as pd

from packages.common.constants import METADATA_COLUMNS
from packages.pipeline.transformation.vote_mapper import (
    VOTE_LABEL_MAP,
    VOTE_SCORE_MAP,
)


def unpivot_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert the UN voting dataset from wide format to long format.

    Each output row represents one country's vote on one resolution.
    """

    country_columns = [
        column
        for column in df.columns
        if column not in METADATA_COLUMNS
    ]

    long_df = df.melt(
        id_vars=METADATA_COLUMNS,
        value_vars=country_columns,
        var_name="Country",
        value_name="VoteCode",
    )

    # Remove rows without a recorded vote
    long_df = long_df.dropna(subset=["VoteCode"])

    # Normalize raw vote codes
    long_df["VoteCode"] = (
        long_df["VoteCode"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Fast vectorized mapping
    long_df["VoteLabel"] = long_df["VoteCode"].map(VOTE_LABEL_MAP)
    long_df["VoteScore"] = long_df["VoteCode"].map(VOTE_SCORE_MAP)

    # Reorder columns
    ordered_columns = (
        METADATA_COLUMNS
        + [
            "Country",
            "VoteCode",
            "VoteLabel",
            "VoteScore",
        ]
    )

    long_df = long_df[ordered_columns]

    return long_df.reset_index(drop=True)