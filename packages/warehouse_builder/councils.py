"""
Build the council dimension.
"""

from __future__ import annotations

import pandas as pd


def build_council_dimension(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the council dimension.

    Parameters
    ----------
    df : pd.DataFrame
        Normalized voting dataset.

    Returns
    -------
    pd.DataFrame
    """

    councils = (
        df["Council"]
        .drop_duplicates()
        .sort_values()
        .reset_index(drop=True)
    )

    return pd.DataFrame(
        {
            "council_id": range(1, len(councils) + 1),
            "council_name": councils,
        }
    )