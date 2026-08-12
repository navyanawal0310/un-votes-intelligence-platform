"""
Fact table construction for official UN voting events.
"""

from __future__ import annotations

import pandas as pd


def build_fact_votes(
    canonical_df: pd.DataFrame,
    dim_body: pd.DataFrame,
    dim_date: pd.DataFrame,
    dim_country: pd.DataFrame,
    dim_resolution: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build the fact_votes warehouse table.

    Grain:
        One Member State vote for one UN voting event.

    Parameters
    ----------
    canonical_df:
        Canonical UN voting dataset.

    dim_body:
        Body dimension.

    dim_date:
        Date dimension.

    dim_country:
        Country dimension.

    dim_resolution:
        Resolution dimension.

    Returns
    -------
    pd.DataFrame
        Fact table containing one row per Member State vote.
    """

    fact = canonical_df.copy()

    # ---------------------------------------------------------
    # 1. Voting event key
    # ---------------------------------------------------------

    fact["vote_event_id"] = fact["undl_id"]

    # ---------------------------------------------------------
    # 2. Resolution key
    # ---------------------------------------------------------

    fact = fact.merge(
        dim_resolution[
            [
                "resolution_id",
                "resolution_code",
            ]
        ],
        left_on="resolution",
        right_on="resolution_code",
        how="left",
        validate="many_to_one",
    )

    # ---------------------------------------------------------
    # 3. Body key
    # ---------------------------------------------------------

    fact = fact.merge(
        dim_body[
            [
                "body_id",
                "body_code",
            ]
        ],
        on="body_code",
        how="left",
        validate="many_to_one",
    )

    # ---------------------------------------------------------
    # 4. Country key
    # ---------------------------------------------------------

    fact = fact.merge(
        dim_country[
            [
                "country_id",
                "ms_code",
            ]
        ],
        on="ms_code",
        how="left",
        validate="many_to_one",
    )

    # ---------------------------------------------------------
    # 5. Date key
    # ---------------------------------------------------------

    fact["date"] = pd.to_datetime(
        fact["date"],
        errors="coerce",
    )

    date_lookup = dim_date[
        [
            "date_id",
            "full_date",
        ]
    ].copy()

    date_lookup["full_date"] = pd.to_datetime(
        date_lookup["full_date"],
        errors="coerce",
    )

    fact = fact.merge(
        date_lookup,
        left_on="date",
        right_on="full_date",
        how="left",
        validate="many_to_one",
    )

    # ---------------------------------------------------------
    # 6. Validate dimension lookups
    # ---------------------------------------------------------

    unresolved = {
        "resolution_id": fact["resolution_id"].isna().sum(),
        "body_id": fact["body_id"].isna().sum(),
        "country_id": fact["country_id"].isna().sum(),
        "date_id": fact["date_id"].isna().sum(),
    }

    unresolved = {
        key: value
        for key, value in unresolved.items()
        if value > 0
    }

    if unresolved:
        raise ValueError(
            "Fact table contains unresolved dimension keys: "
            f"{unresolved}"
        )

    # ---------------------------------------------------------
    # 7. Select warehouse columns
    # ---------------------------------------------------------

    fact = fact[
        [
            "vote_event_id",
            "body_id",
            "resolution_id",
            "country_id",
            "date_id",
            "vote_code",
            "vote_label",
            "vote_score",
        ]
    ]

    # ---------------------------------------------------------
    # 8. Fact-level validation
    # ---------------------------------------------------------

    duplicate_count = fact.duplicated(
        subset=[
            "vote_event_id",
            "country_id",
        ]
    ).sum()

    if duplicate_count > 0:
        raise ValueError(
            "Duplicate country votes detected: "
            f"{duplicate_count}"
        )

    return fact.reset_index(drop=True)