"""
Canonical data contracts for the UN Votes Analyzer.

This module validates datasets at the boundary between
ingestion/transformation and analytical storage.
"""

from __future__ import annotations

import pandas as pd


# ============================================================
# CANONICAL SCHEMA
# ============================================================

REQUIRED_CANONICAL_COLUMNS = {
    "undl_id",
    "ms_code",
    "ms_name",
    "ms_vote",
    "date",
    "resolution",
    "draft",
    "meeting",
    "subjects",
    "vote_note",
    "total_yes",
    "total_no",
    "total_abstentions",
    "total_non_voting",
    "total_ms",
    "undl_link",
    "body_code",
    "vote_code",
    "vote_label",
    "vote_score",
}


# ============================================================
# VALIDATION
# ============================================================

def validate_canonical_schema(
    df: pd.DataFrame,
) -> None:
    """
    Validate a canonical UN voting DataFrame.

    Raises ValueError when the dataset violates the
    canonical platform contract.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "Canonical dataset must be a pandas DataFrame."
        )

    if df.empty:
        raise ValueError(
            "Canonical dataset is empty."
        )

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    missing = (
        REQUIRED_CANONICAL_COLUMNS
        - set(df.columns)
    )

    if missing:
        raise ValueError(
            "Canonical dataset missing required "
            f"columns: {sorted(missing)}"
        )

    # --------------------------------------------------------
    # Identifier validation
    # --------------------------------------------------------

    if df["undl_id"].isna().any():
        raise ValueError(
            "Canonical dataset contains missing undl_id values."
        )

    if df["ms_code"].isna().any():
        raise ValueError(
            "Canonical dataset contains missing ms_code values."
        )

    if df["body_code"].isna().any():
        raise ValueError(
            "Canonical dataset contains missing body_code values."
        )

    # --------------------------------------------------------
    # Body validation
    # --------------------------------------------------------

    valid_bodies = {
        "GA",
        "SC",
    }

    invalid_bodies = set(
        df["body_code"]
        .dropna()
        .astype(str)
        .str.upper()
        .unique()
    ) - valid_bodies

    if invalid_bodies:
        raise ValueError(
            "Canonical dataset contains invalid body_code "
            f"values: {sorted(invalid_bodies)}"
        )

    # --------------------------------------------------------
    # Vote-code validation
    # --------------------------------------------------------

    valid_vote_codes = {
        "Y",   # YES
        "N",   # NO
        "A",   # ABSTAIN
        "X",   # NON-VOTING / unavailable
    }

    observed_vote_codes = set(
        df["vote_code"]
        .dropna()
        .astype(str)
        .str.upper()
        .unique()
    )

    invalid_vote_codes = (
        observed_vote_codes
        - valid_vote_codes
    )

    if invalid_vote_codes:
        raise ValueError(
            "Canonical dataset contains invalid vote_code "
            f"values: {sorted(invalid_vote_codes)}"
        )

    # --------------------------------------------------------
    # Vote-score validation
    #
    # Y = +1
    # A =  0
    # N = -1
    # X = NaN
    # --------------------------------------------------------

    non_null_scores = df[
        "vote_score"
    ].dropna()

    invalid_scores = non_null_scores[
        ~non_null_scores.isin(
            [-1.0, 0.0, 1.0]
        )
    ]

    if not invalid_scores.empty:
        raise ValueError(
            "Canonical dataset contains invalid "
            "vote_score values. Expected -1, 0, 1 "
            f"(or NaN): {sorted(invalid_scores.unique())}"
        )

    # --------------------------------------------------------
    # Vote-code / score consistency
    # --------------------------------------------------------

    expected_scores = {
        "Y": 1.0,
        "N": -1.0,
        "A": 0.0,
    }

    for vote_code, expected_score in expected_scores.items():

        mask = (
            df["vote_code"]
            .astype(str)
            .str.upper()
            == vote_code
        )

        if mask.any():

            observed = df.loc[
                mask,
                "vote_score",
            ]

            invalid = observed[
                observed != expected_score
            ]

            if not invalid.empty:
                raise ValueError(
                    f"vote_code '{vote_code}' has "
                    f"inconsistent vote_score values."
                )

    # --------------------------------------------------------
    # Date validation
    # --------------------------------------------------------

    if not pd.api.types.is_datetime64_any_dtype(
        df["date"]
    ):
        raise ValueError(
            "Canonical dataset 'date' column must "
            "be datetime."
        )

    if df["date"].isna().all():
        raise ValueError(
            "Canonical dataset contains no valid dates."
        )

    # --------------------------------------------------------
    # Aggregate vote-count validation
    # --------------------------------------------------------

    count_columns = [
        "total_yes",
        "total_no",
        "total_abstentions",
        "total_non_voting",
        "total_ms",
    ]

    for column in count_columns:

        numeric = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        if numeric.isna().all():
            raise ValueError(
                f"Column '{column}' contains no "
                "valid numeric values."
            )

        if (numeric.dropna() < 0).any():
            raise ValueError(
                f"Column '{column}' contains negative "
                "vote counts."
            )

    # --------------------------------------------------------
    # Basic population consistency
    # --------------------------------------------------------

    total = (
        pd.to_numeric(
            df["total_yes"],
            errors="coerce",
        ).fillna(0)
        +
        pd.to_numeric(
            df["total_no"],
            errors="coerce",
        ).fillna(0)
        +
        pd.to_numeric(
            df["total_abstentions"],
            errors="coerce",
        ).fillna(0)
        +
        pd.to_numeric(
            df["total_non_voting"],
            errors="coerce",
        ).fillna(0)
    )

    total_ms = pd.to_numeric(
        df["total_ms"],
        errors="coerce",
    )

    inconsistent_totals = (
        total_ms.notna()
        & (total != total_ms)
    )

    if inconsistent_totals.any():
        raise ValueError(
            "Canonical dataset contains inconsistent "
            "vote totals."
        )

    print(
        f"[OK] Canonical schema validated: "
        f"{len(df):,} rows"
    )