from __future__ import annotations

import pandas as pd


def temporal_alignment(
    alignment: pd.DataFrame,
    window: int = 5,
    min_observations: int = 3,
) -> pd.DataFrame:
    """
    Calculate rolling temporal alignment between two countries.

    Alignment is aggregated across issue-year observations
    within a rolling year window.
    """

    if alignment.empty:
        return pd.DataFrame()

    df = alignment.copy()

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "year",
            "alignment_score",
        ]
    )

    df["year"] = df["year"].astype(int)

    rows = []

    for (country_a, country_b), pair in df.groupby(
        ["country_a", "country_b"]
    ):

        min_year = int(pair["year"].min())
        max_year = int(pair["year"].max())

        for end_year in range(
            min_year,
            max_year + 1,
        ):

            start_year = (
                end_year - window + 1
            )

            subset = pair[
                (pair["year"] >= start_year)
                & (pair["year"] <= end_year)
            ]

            if len(subset) < min_observations:
                continue

            rows.append(
                {
                    "country_a": country_a,
                    "country_b": country_b,
                    "window_start": start_year,
                    "window_end": end_year,
                    "observations": len(subset),
                    "mean_alignment": (
                        subset[
                            "alignment_score"
                        ].mean()
                    ),
                    "mean_divergence": (
                        subset[
                            "absolute_divergence"
                        ].mean()
                    ),
                    "directional_agreement": (
                        subset[
                            "directional_agreement"
                        ].mean()
                    ),
                }
            )

    return pd.DataFrame(rows)