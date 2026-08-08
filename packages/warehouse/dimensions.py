"""
Warehouse dimension builders.
"""

from __future__ import annotations

import pandas as pd


def build_dim_council(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the council dimension.
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
def build_dim_date(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the date dimension.
    """

    dates = (
        pd.to_datetime(df["Date"], format="mixed")
        .drop_duplicates()
        .sort_values()
    )

    dim_date = pd.DataFrame(
        {
            "full_date": dates,
        }
    )

    dim_date["date_id"] = range(1, len(dim_date) + 1)

    dim_date["year"] = dim_date["full_date"].dt.year
    dim_date["month"] = dim_date["full_date"].dt.month
    dim_date["quarter"] = dim_date["full_date"].dt.quarter
    dim_date["day"] = dim_date["full_date"].dt.day

    dim_date["month_name"] = (
        dim_date["full_date"]
        .dt.month_name()
    )

    dim_date["day_name"] = (
        dim_date["full_date"]
        .dt.day_name()
    )

    return dim_date[
        [
            "date_id",
            "full_date",
            "year",
            "quarter",
            "month",
            "month_name",
            "day",
            "day_name",
        ]
    ]