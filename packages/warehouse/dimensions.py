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
    Build the date dimension from the voting dataset.

    The source dataset contains mixed date representations, so
    parsing is performed explicitly with format='mixed'.

    Raises
    ------
    ValueError
        If any source date cannot be parsed.
    """

    parsed_dates = pd.to_datetime(
        df["Date"],
        format="mixed",
        errors="coerce",
    )

    invalid_dates = df.loc[
        parsed_dates.isna(),
        "Date",
    ].drop_duplicates()

    if not invalid_dates.empty:
        examples = invalid_dates.head(10).tolist()

        raise ValueError(
            "Unable to parse source date values. "
            f"Examples: {examples}"
        )

    dates = (
        parsed_dates
        .drop_duplicates()
        .sort_values()
        .reset_index(drop=True)
    )

    dim_date = pd.DataFrame(
        {
            "date_id": range(1, len(dates) + 1),
            "full_date": dates,
        }
    )

    dim_date["year"] = dim_date["full_date"].dt.year
    dim_date["quarter"] = dim_date["full_date"].dt.quarter
    dim_date["month"] = dim_date["full_date"].dt.month
    dim_date["month_name"] = (
        dim_date["full_date"].dt.month_name()
    )
    dim_date["day"] = dim_date["full_date"].dt.day
    dim_date["day_name"] = (
        dim_date["full_date"].dt.day_name()
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

def build_dim_country(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the country dimension from country columns
    present in the normalized voting dataset.

    Country IDs are assigned deterministically based on
    alphabetical ordering of the observed country names.
    """

    countries = (
        df["Country"]
        .dropna()
        .astype(str)
        .str.strip()
        .drop_duplicates()
        .sort_values()
        .reset_index(drop=True)
    )

    dim_country = pd.DataFrame(
        {
            "country_id": range(1, len(countries) + 1),
            "country_name": countries,
        }
    )

    return dim_country