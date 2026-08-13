"""
Warehouse dimension builders for official UN voting datasets.
"""

from __future__ import annotations

import pandas as pd


def build_dim_body(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the UN body dimension.

    Expected input:
        body_code

    Example:
        GA -> General Assembly
        SC -> Security Council
    """

    body_names = {
        "GA": "General Assembly",
        "SC": "Security Council",
    }

    bodies = (
        df["body_code"]
        .dropna()
        .astype(str)
        .str.strip()
        .drop_duplicates()
        .sort_values()
        .reset_index(drop=True)
    )

    unknown_bodies = set(bodies) - set(body_names)

    if unknown_bodies:
        raise ValueError(
            f"Unknown UN body codes: {sorted(unknown_bodies)}"
        )

    return pd.DataFrame(
        {
            "body_id": range(1, len(bodies) + 1),
            "body_code": bodies,
            "body_name": bodies.map(body_names),
        }
    )


def build_dim_country(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the country dimension from official UN Member State codes.

    The UN dataset preserves the official Member State name at the
    time of each vote. Therefore, the same ms_code may legitimately
    appear with different names across history.

    The country dimension uses ms_code as the stable natural key and
    retains the most recently observed name for each Member State.
    """

    countries = (
        df[
            [
                "ms_code",
                "ms_name",
                "date",
            ]
        ]
        .dropna(subset=["ms_code"])
        .copy()
    )

    countries["ms_code"] = (
        countries["ms_code"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    countries["ms_name"] = (
        countries["ms_name"]
        .astype(str)
        .str.strip()
    )

    countries["date"] = pd.to_datetime(
        countries["date"],
        errors="coerce",
    )

    # Sort chronologically so the final observed name
    # becomes the canonical name for the country dimension.
    countries = countries.sort_values(
        ["ms_code", "date"]
    )

    countries = (
        countries
        .drop_duplicates(
            subset=["ms_code"],
            keep="last",
        )
        .sort_values("ms_code")
        .reset_index(drop=True)
    )

    dim_country = pd.DataFrame(
        {
            "country_id": range(
                1,
                len(countries) + 1,
            ),
            "ms_code": countries["ms_code"],
            "country_name": countries["ms_name"],
        }
    )

    return dim_country
    
def build_dim_date(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the date dimension from official UN voting dates.

    Only dates actually represented in the voting dataset are included.
    """

    dates = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    if dates.isna().any():
        raise ValueError(
            "Cannot build dim_date: invalid dates found."
        )

    dates = (
        dates
        .drop_duplicates()
        .sort_values()
        .reset_index(drop=True)
    )

    dim_date = pd.DataFrame(
        {
            "full_date": dates,
        }
    )

    dim_date.insert(
        0,
        "date_id",
        range(1, len(dim_date) + 1),
    )

    dim_date["year"] = dim_date["full_date"].dt.year
    dim_date["quarter"] = dim_date["full_date"].dt.quarter
    dim_date["month"] = dim_date["full_date"].dt.month
    dim_date["month_name"] = dim_date["full_date"].dt.month_name()
    dim_date["day"] = dim_date["full_date"].dt.day
    dim_date["day_name"] = dim_date["full_date"].dt.day_name()

    dim_date["date_precision"] = "FULL_DATE"

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

def build_dim_resolution(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the UN resolution dimension.

    Each adopted resolution is identified by its official
    resolution symbol.

    Example:
        A/RES/58/20
    """

    resolutions = (
        df[
            [
                "undl_id",
                "resolution",
                "title",
                "agenda_title",
                "subjects",
                "session",
                "undl_link",
            ]
        ]
        .drop_duplicates()
        .sort_values("resolution")
        .reset_index(drop=True)
    )

    # A resolution should have one consistent title.
    title_counts = (
        resolutions
        .groupby("resolution")["title"]
        .nunique(dropna=False)
    )

    conflicting_titles = title_counts[
        title_counts > 1
    ]

    if not conflicting_titles.empty:
        raise ValueError(
            "Resolution codes map to multiple titles: "
            f"{conflicting_titles.index.tolist()[:10]}"
        )

    # One row per resolution.
    dim_resolution = (
        resolutions
        .drop_duplicates(subset=["resolution"])
        .reset_index(drop=True)
    )

    dim_resolution.insert(
        0,
        "resolution_id",
        range(1, len(dim_resolution) + 1),
    )

    return dim_resolution.rename(
        columns={
            "resolution": "resolution_code",
            "title": "resolution_title",
        }
    )[
        [
            "resolution_id",
            "resolution_code",
            "resolution_title",
            "agenda_title",
            "subjects",
            "session",
            "undl_id",
            "undl_link",
        ]
    ]