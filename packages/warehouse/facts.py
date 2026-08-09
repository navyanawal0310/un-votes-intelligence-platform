"""
Fact table construction for UN voting events.
"""

from __future__ import annotations

import pandas as pd


def build_fact_votes(
    long_df: pd.DataFrame,
    dim_council: pd.DataFrame,
    dim_date: pd.DataFrame,
    dim_country: pd.DataFrame,
    dim_resolution: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build the fact_votes table.

    Grain:
        One country vote for one voting event.

    Parameters
    ----------
    long_df : pd.DataFrame
        Normalized long-format voting data.
    dim_council : pd.DataFrame
        Council dimension.
    dim_date : pd.DataFrame
        Date dimension.
    dim_country : pd.DataFrame
        Country dimension.
    dim_resolution : pd.DataFrame
        Resolution dimension.

    Returns
    -------
    pd.DataFrame
        Fact table containing one row per country vote.
    """

    fact = long_df.copy()

    # ---------------------------------------------------------
    # Voting event key
    # ---------------------------------------------------------

    fact["vote_event_id"] = fact["token"]

    # ---------------------------------------------------------
    # Resolution key
    # ---------------------------------------------------------

    fact = fact.merge(
        dim_resolution[
            [
                "resolution_id",
                "resolution_code",
            ]
        ],
        left_on="Resolution",
        right_on="resolution_code",
        how="left",
        validate="many_to_one",
    )

    # ---------------------------------------------------------
    # Council key
    # ---------------------------------------------------------

    fact = fact.merge(
        dim_council[
            [
                "council_id",
                "council_name",
            ]
        ],
        left_on="Council",
        right_on="council_name",
        how="left",
        validate="many_to_one",
    )

    # ---------------------------------------------------------
    # Country key
    # ---------------------------------------------------------

    fact = fact.merge(
        dim_country[
            [
                "country_id",
                "country_name",
            ]
        ],
        left_on="Country",
        right_on="country_name",
        how="left",
        validate="many_to_one",
    )

    # ---------------------------------------------------------
    # Date key
    # ---------------------------------------------------------

        # ---------------------------------------------------------
    # Date key
    # ---------------------------------------------------------

    fact["DateRaw"] = fact["Date"].astype(str).str.strip()

    # Determine whether the source contains a full date or
    # only a year.
    fact["date_precision"] = fact["DateRaw"].str.fullmatch(
        r"\d{4}"
    ).map(
        {True: "YEAR_ONLY", False: "FULL_DATE"}
    )

    # Build a stable date join key.
    fact["date_join_key"] = fact.apply(
        lambda row: (
            f"YEAR:{row['DateRaw']}"
            if row["date_precision"] == "YEAR_ONLY"
            else f"DATE:{row['DateRaw']}"
        ),
        axis=1,
    )

    date_lookup = dim_date.copy()

    date_lookup["date_join_key"] = date_lookup.apply(
        lambda row: (
            f"YEAR:{int(row['year'])}"
            if row["date_precision"] == "YEAR_ONLY"
            else f"DATE:{row['full_date'].strftime('%Y-%m-%d')}"
        ),
        axis=1,
    )

    fact = fact.merge(
        date_lookup[
            [
                "date_id",
                "date_join_key",
            ]
        ],
        on="date_join_key",
        how="left",
        validate="many_to_one",
    )

    fact = fact.drop(
        columns=[
            "DateRaw",
            "date_precision",
            "date_join_key",
        ]
    )
    # ---------------------------------------------------------
    # Select warehouse columns
    # ---------------------------------------------------------

    fact = fact[
        [
            "vote_event_id",
            "resolution_id",
            "country_id",
            "council_id",
            "date_id",
            "VoteCode",
            "VoteLabel",
            "VoteScore",
        ]
    ]

    fact = fact.rename(
        columns={
            "VoteCode": "vote_code",
            "VoteLabel": "vote_label",
            "VoteScore": "vote_score",
        }
    )

    return fact.reset_index(drop=True)