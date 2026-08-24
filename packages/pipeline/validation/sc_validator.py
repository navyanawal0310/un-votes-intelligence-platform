"""
Security Council Dataset Validator
===================================

Validates the canonical Security Council voting dataframe
produced by sc_loader.py.

The validator operates AFTER ingestion and normalization.

It validates:
    - canonical schema
    - identifiers
    - dates
    - vote scores
    - vote labels
    - vote codes
    - basic data quality

It does not perform analytical transformations.
"""

from __future__ import annotations

import pandas as pd


# ============================================================
# CANONICAL SCHEMA
# ============================================================

REQUIRED_COLUMNS = {
    "undl_id",
    "ms_code",
    "ms_name",
    "permanent_member",
    "ms_vote",
    "date",
    "resolution",
    "meeting",
    "description",
    "total_yes",
    "total_no",
    "total_abstentions",
    "total_non_voting",
    "total_ms",
    "modality",
    "undl_link",

    # Normalized analytical fields
    "body_code",
    "vote_code",
    "vote_label",
    "vote_score",
}


# ============================================================
# VALIDATE SC DATASET
# ============================================================

def validate_sc_dataset(df: pd.DataFrame) -> bool:
    """
    Validate canonical Security Council voting data.

    Parameters
    ----------
    df:
        Canonical dataframe returned by load_sc_dataset().

    Returns
    -------
    bool
        True if validation succeeds.

    Raises
    ------
    TypeError
        If input is not a pandas DataFrame.

    ValueError
        If schema or data-quality validation fails.
    """

    # --------------------------------------------------------
    # Type
    # --------------------------------------------------------

    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            "Security Council dataset must be a pandas DataFrame."
        )

    # --------------------------------------------------------
    # Empty dataset
    # --------------------------------------------------------

    if df.empty:
        raise ValueError(
            "Security Council dataset is empty."
        )

    # --------------------------------------------------------
    # Schema validation
    # --------------------------------------------------------

    missing = REQUIRED_COLUMNS - set(df.columns)

    if missing:
        raise ValueError(
            "Security Council dataset missing required "
            f"columns: {sorted(missing)}"
        )

    # --------------------------------------------------------
    # Required fields must not be entirely null
    # --------------------------------------------------------

    critical_columns = [
        "undl_id",
        "ms_code",
        "ms_name",
        "date",
        "resolution",
        "vote_code",
        "vote_label",
        "vote_score",
    ]

    for column in critical_columns:

        if df[column].isna().all():

            raise ValueError(
                f"Security Council column '{column}' "
                "contains no usable values."
            )

    # --------------------------------------------------------
    # Country/member code validation
    # --------------------------------------------------------

    if (
        df["ms_code"]
        .astype(str)
        .str.strip()
        .eq("")
        .any()
    ):

        raise ValueError(
            "Security Council dataset contains empty "
            "member-state codes."
        )

    # --------------------------------------------------------
    # Date validation
    # --------------------------------------------------------

    dates = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    invalid_dates = dates.isna().sum()

    if invalid_dates > 0:

        raise ValueError(
            "Security Council dataset contains "
            f"{invalid_dates:,} invalid date values."
        )

    # --------------------------------------------------------
    # Vote score validation
    # --------------------------------------------------------

    if not pd.api.types.is_numeric_dtype(
        df["vote_score"]
    ):

        raise ValueError(
            "Security Council 'vote_score' must be numeric."
        )

    # --------------------------------------------------------
# Vote score validation
# --------------------------------------------------------

    if not pd.api.types.is_numeric_dtype(
        df["vote_score"]
    ):
        raise ValueError(
            "Security Council 'vote_score' must be numeric."
        )

    # Canonical voting scale:
    #
    # YES      = +1
    # ABSTAIN  =  0
    # NO       = -1
    #
    # NaN is permitted for votes that cannot be mapped
    # to the canonical voting scale.

    invalid_scores = (
        df["vote_score"].notna()
        & ~df["vote_score"].between(
            -1.0,
            1.0,
            inclusive="both",
        )
    ).sum()

    if invalid_scores > 0:
        raise ValueError(
            "Security Council dataset contains "
            f"{invalid_scores:,} vote_score values outside "
            "the canonical range [-1, 1]."
        )

    if invalid_scores > 0:

        raise ValueError(
            "Security Council dataset contains "
            f"{invalid_scores:,} vote_score values outside "
            "the canonical range [0, 1]."
        )
    # --------------------------------------------------------
    # Vote-score mapping consistency
    # --------------------------------------------------------

    score_by_code = {
        "Y": 1.0,
        "YES": 1.0,
        "N": -1.0,
        "NO": -1.0,
        "A": 0.0,
        "ABSTAIN": 0.0,
        "ABSTENTION": 0.0,
    }

    for vote_code, expected_score in score_by_code.items():

        mask = (
            df["vote_code"]
            .astype(str)
            .str.upper()
            .str.strip()
            .eq(vote_code)
        )

        if mask.any():

            observed = df.loc[
                mask,
                "vote_score"
            ]

            invalid_mapping = (
                observed.notna()
                & (observed != expected_score)
            ).sum()

            if invalid_mapping > 0:
                raise ValueError(
                    f"Inconsistent vote_score mapping for "
                    f"vote_code '{vote_code}': "
                    f"{invalid_mapping:,} invalid rows."
                )
    # --------------------------------------------------------
    # Vote-code validation
    # --------------------------------------------------------

    valid_vote_codes = {
        "Y",
        "N",
        "A",
        "X",
        "NV",
        "YES",
        "NO",
        "ABSTAIN",
        "ABSTENTION",
    }

    observed_codes = set(
        df["vote_code"]
        .dropna()
        .astype(str)
        .str.upper()
        .str.strip()
        .unique()
    )

    unexpected_codes = (
        observed_codes - valid_vote_codes
    )

    # Do not fail on unexpected source codes immediately.
    # Report them because official UN datasets may contain
    # additional representations that should be handled
    # deliberately by the canonical transformation layer.
    if unexpected_codes:

        print(
            "WARNING: Unexpected SC vote codes detected: "
            f"{sorted(unexpected_codes)}"
        )

    # --------------------------------------------------------
    # Body code
    # --------------------------------------------------------

    body_codes = set(
        df["body_code"]
        .dropna()
        .astype(str)
        .str.upper()
        .str.strip()
        .unique()
    )

    if body_codes != {"SC"}:

        raise ValueError(
            "Security Council dataset contains unexpected "
            f"body_code values: {sorted(body_codes)}"
        )

    # --------------------------------------------------------
    # Duplicate detection
    # --------------------------------------------------------

    duplicate_keys = [
        "undl_id",
        "ms_code",
    ]

    duplicate_count = df.duplicated(
        subset=duplicate_keys
    ).sum()

    if duplicate_count > 0:

        raise ValueError(
            "Security Council dataset contains "
            f"{duplicate_count:,} duplicate "
            "undl_id/member-state observations."
        )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    print(
        "Security Council dataset validation: PASSED"
    )

    print(
        f"Rows validated: {len(df):,}"
    )

    print(
        f"Countries represented: "
        f"{df['ms_code'].nunique():,}"
    )

    print(
        f"UN voting events: "
        f"{df['undl_id'].nunique():,}"
    )

    print(
        f"Date range: "
        f"{dates.min().date()} → {dates.max().date()}"
    )

    return True