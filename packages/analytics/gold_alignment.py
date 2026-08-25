from __future__ import annotations

import pandas as pd


def calculate_pair_alignment(
    pair_votes: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate voting alignment directly from Gold
    country-pair observations.

    Alignment:
        1 - |vote_score_a - vote_score_b| / 2

    vote_score ∈ {-1, 0, 1}
    therefore alignment ∈ [0, 1].
    """

    required = {
        "undl_id",
        "year",
        "body_code",
        "resolution",
        "country_a",
        "country_b",
        "pair",
        "vote_score_a",
        "vote_score_b",
    }

    missing = required - set(pair_votes.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    if pair_votes.empty:
        return pd.DataFrame()

    df = pair_votes.copy()

    df["vote_score_a"] = pd.to_numeric(
        df["vote_score_a"],
        errors="coerce",
    )

    df["vote_score_b"] = pd.to_numeric(
        df["vote_score_b"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "vote_score_a",
            "vote_score_b",
        ]
    )

    valid_scores = {-1.0, 0.0, 1.0}

    if not df["vote_score_a"].isin(valid_scores).all():
        raise ValueError(
            "vote_score_a contains non-canonical values."
        )

    if not df["vote_score_b"].isin(valid_scores).all():
        raise ValueError(
            "vote_score_b contains non-canonical values."
        )

    df["absolute_divergence"] = (
        df["vote_score_a"]
        - df["vote_score_b"]
    ).abs()

    df["alignment_score"] = (
        1.0
        - df["absolute_divergence"] / 2.0
    )

    df["directional_agreement"] = (
        df["vote_score_a"]
        * df["vote_score_b"]
        > 0
    ).astype("int8")

    return df[
        [
            "undl_id",
            "year",
            "body_code",
            "resolution",
            "country_a",
            "country_b",
            "pair",
            "vote_score_a",
            "vote_score_b",
            "absolute_divergence",
            "alignment_score",
            "directional_agreement",
        ]
    ].sort_values(
        [
            "pair",
            "year",
            "undl_id",
        ]
    ).reset_index(drop=True)


def summarize_pair_alignment(
    alignment: pd.DataFrame,
) -> pd.DataFrame:
    """
    Produce country-pair/year analytical summaries.
    """

    if alignment.empty:
        return pd.DataFrame()

    result = (
        alignment
        .groupby(
            [
                "country_a",
                "country_b",
                "pair",
                "body_code",
                "year",
            ],
            as_index=False,
        )
        .agg(
            observations=(
                "alignment_score",
                "count",
            ),
            mean_alignment=(
                "alignment_score",
                "mean",
            ),
            median_alignment=(
                "alignment_score",
                "median",
            ),
            std_alignment=(
                "alignment_score",
                "std",
            ),
            mean_divergence=(
                "absolute_divergence",
                "mean",
            ),
            directional_agreement=(
                "directional_agreement",
                "mean",
            ),
        )
    )

    result["std_alignment"] = (
        result["std_alignment"]
        .fillna(0.0)
    )

    return result.sort_values(
        [
            "pair",
            "year",
        ]
    ).reset_index(drop=True)