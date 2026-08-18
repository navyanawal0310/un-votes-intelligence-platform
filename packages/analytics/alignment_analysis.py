from __future__ import annotations

import pandas as pd


def alignment_by_issue(
    alignment: pd.DataFrame,
    min_observations: int = 3,
) -> pd.DataFrame:

    if alignment.empty:
        return pd.DataFrame()

    result = (
        alignment
        .groupby(
            ["country_a", "country_b", "issue"]
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
            mean_divergence=(
                "absolute_divergence",
                "mean",
            ),
            directional_agreement=(
                "directional_agreement",
                "mean",
            ),
        )
        .reset_index()
    )

    result = result[
        result["observations"] >= min_observations
    ].copy()

    result["reportable"] = (
        result["observations"] >= 5
    )

    return result.sort_values(
        [
            "country_a",
            "country_b",
            "mean_divergence",
        ],
        ascending=[
            True,
            True,
            False,
        ],
    ).reset_index(drop=True)