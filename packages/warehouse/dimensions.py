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
    Build the date dimension while preserving source date precision.

    Full dates are stored as actual dates.
    Year-only source values are represented with a NULL full_date
    and their corresponding year.
    """

    raw_dates = df["Date"].astype(str).str.strip()

    year_only_mask = raw_dates.str.fullmatch(r"\d{4}")

    parsed_dates = pd.to_datetime(
        raw_dates.where(~year_only_mask),
        format="mixed",
        errors="coerce",
    )

    invalid_mask = (
        parsed_dates.isna()
        & ~year_only_mask
    )

    if invalid_mask.any():
        invalid_values = (
            raw_dates.loc[invalid_mask]
            .drop_duplicates()
            .head(10)
            .tolist()
        )

        raise ValueError(
            "Unable to parse source date values. "
            f"Examples: {invalid_values}"
        )

    records: list[dict] = []

    # Full-precision dates
    full_dates = (
        parsed_dates.loc[~year_only_mask]
        .drop_duplicates()
        .sort_values()
    )

    for date in full_dates:
        records.append(
            {
                "full_date": date,
                "year": date.year,
                "date_precision": "FULL_DATE",
            }
        )

    # Year-only dates
    year_only_values = (
        raw_dates.loc[year_only_mask]
        .astype(int)
        .drop_duplicates()
        .sort_values()
    )

    for year in year_only_values:
        records.append(
            {
                "full_date": pd.NaT,
                "year": year,
                "date_precision": "YEAR_ONLY",
            }
        )

    dim_date = pd.DataFrame(records)

    dim_date = dim_date.sort_values(
        ["year", "full_date", "date_precision"],
        na_position="last",
    ).reset_index(drop=True)

    dim_date["date_id"] = range(
        1,
        len(dim_date) + 1,
    )

    dim_date["quarter"] = (
        dim_date["full_date"]
        .dt.quarter
    )

    dim_date["month"] = (
        dim_date["full_date"]
        .dt.month
    )

    dim_date["month_name"] = (
        dim_date["full_date"]
        .dt.month_name()
    )

    dim_date["day"] = (
        dim_date["full_date"]
        .dt.day
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
            "date_precision",
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
def build_dim_resolution(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the resolution dimension.

    Resolution codes identify the logical resolution, while the
    source token identifies an individual voting event.

    Parameters
    ----------
    df : pd.DataFrame
        Normalized voting dataset.

    Returns
    -------
    pd.DataFrame
        Resolution dimension.
    """

    resolution_columns = [
        "Resolution",
        "Title",
    ]

    resolutions = (
        df[resolution_columns]
        .drop_duplicates()
        .sort_values("Resolution")
        .reset_index(drop=True)
    )

    # A resolution code should map to exactly one title.
    title_counts = (
        resolutions
        .groupby("Resolution")["Title"]
        .nunique(dropna=False)
    )

    conflicting_resolutions = title_counts[
        title_counts > 1
    ]

    if not conflicting_resolutions.empty:
        raise ValueError(
            "Resolution codes map to multiple titles: "
            f"{conflicting_resolutions.index.tolist()}"
        )

    dim_resolution = (
        resolutions
        .drop_duplicates(subset=["Resolution"])
        .reset_index(drop=True)
    )

    dim_resolution.insert(
        0,
        "resolution_id",
        range(1, len(dim_resolution) + 1),
    )

    dim_resolution = dim_resolution.rename(
        columns={
            "Resolution": "resolution_code",
            "Title": "resolution_title",
        }
    )

    return dim_resolution[
        [
            "resolution_id",
            "resolution_code",
            "resolution_title",
        ]
    ]