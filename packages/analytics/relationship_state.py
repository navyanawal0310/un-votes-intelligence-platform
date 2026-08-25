"""
Generic country-to-country relationship state.

Builds a yearly relationship intelligence layer from
existing country-pair analytical observations.

This module is intentionally source-agnostic so future
evidence sources such as speeches, geopolitical events,
and current affairs can be integrated without redesign.
"""

from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = {
    "country_a",
    "country_b",
    "year",
    "mean_alignment",
    "mean_divergence",
    "directional_agreement",
}


def build_relationship_state(
    alignment: pd.DataFrame,
    change_episodes: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Build yearly country-pair relationship states.

    Grain:
        country_a × country_b × year

    Relationship state is derived from existing analytical
    evidence rather than raw voting records.

    The schema deliberately includes generic evidence and
    provenance fields for future data-source integration.
    """

    missing = REQUIRED_COLUMNS - set(alignment.columns)

    if missing:
        raise ValueError(
            f"Relationship input missing required columns: "
            f"{sorted(missing)}"
        )

    df = alignment.copy()

    df["country_a"] = (
        df["country_a"].astype(str).str.upper().str.strip()
    )

    df["country_b"] = (
        df["country_b"].astype(str).str.upper().str.strip()
    )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    # Base relationship signal.
    #
    # Alignment is the primary signal.
    # Directional agreement provides an additional
    # behavioural confirmation.
    df["relationship_score"] = (
        0.7 * df["mean_alignment"]
        + 0.3 * df["directional_agreement"]
    )

    df["relationship_score"] = (
        df["relationship_score"]
        .clip(0.0, 1.0)
        .round(6)
    )

    df["relationship_direction"] = "ALIGNED"

    df.loc[
        df["relationship_score"] < 0.40,
        "relationship_direction",
    ] = "DIVERGENT"

    df.loc[
        (df["relationship_score"] >= 0.40)
        & (df["relationship_score"] < 0.65),
        "relationship_direction",
    ] = "MIXED"

    # Evidence count.
    if "observations" in df.columns:
        df["evidence_count"] = (
            pd.to_numeric(
                df["observations"],
                errors="coerce",
            )
            .fillna(0)
            .astype(int)
        )
    else:
        df["evidence_count"] = 0

    # Change-episode evidence.
    df["change_episode_count"] = 0
    df["confirmed_episode_count"] = 0

    if change_episodes is not None and not change_episodes.empty:

        episodes = change_episodes.copy()

        episodes["country_a"] = (
            episodes["country_a"]
            .astype(str)
            .str.upper()
            .str.strip()
        )

        episodes["country_b"] = (
            episodes["country_b"]
            .astype(str)
            .str.upper()
            .str.strip()
        )

        # An episode contributes to every year covered by
        # its temporal window.
        expanded = []

        for row in episodes.itertuples(index=False):

            start = int(row.episode_start)
            end = int(row.episode_end)

            for year in range(start, end + 1):

                expanded.append(
                    {
                        "country_a": row.country_a,
                        "country_b": row.country_b,
                        "year": year,
                        "episode_count": 1,
                        "confirmed_count": int(
                            getattr(
                                row,
                                "confirmed_detections",
                                0,
                            )
                            > 0
                        ),
                    }
                )

        if expanded:

            episode_years = pd.DataFrame(expanded)

            episode_years = (
                episode_years
                .groupby(
                    [
                        "country_a",
                        "country_b",
                        "year",
                    ],
                    as_index=False,
                )
                .agg(
                    episode_count=(
                        "episode_count",
                        "sum",
                    ),
                    confirmed_count=(
                        "confirmed_count",
                        "sum",
                    ),
                )
            )

            df = df.merge(
                episode_years,
                on=[
                    "country_a",
                    "country_b",
                    "year",
                ],
                how="left",
            )

            df["change_episode_count"] = (
                df["episode_count"]
                .fillna(0)
                .astype(int)
            )

            df["confirmed_episode_count"] = (
                df["confirmed_count"]
                .fillna(0)
                .astype(int)
            )

            df.drop(
                columns=[
                    "episode_count",
                    "confirmed_count",
                ],
                inplace=True,
            )

    # Generic evidence/provenance fields.
    df["evidence_source"] = "UN_VOTING"
    df["provenance"] = "UN_VOTES_ANALYZER"

    return df[
        [
            "country_a",
            "country_b",
            "year",
            "relationship_score",
            "relationship_direction",
            "mean_alignment",
            "mean_divergence",
            "directional_agreement",
            "evidence_count",
            "change_episode_count",
            "confirmed_episode_count",
            "evidence_source",
            "provenance",
        ]
    ].sort_values(
        [
            "country_a",
            "country_b",
            "year",
        ]
    ).reset_index(drop=True)