from __future__ import annotations

import duckdb
import pandas as pd

from packages.analytics.issue_positions import issue_positions


def country_alignment(
    con: duckdb.DuckDBPyConnection,
    country_a: str,
    country_b: str,
    min_events: int = 3,
) -> pd.DataFrame:
    """
    Compare two countries' voting positions by issue and year.

    Alignment:
        1 - |score_a - score_b| / 2

    Since position_score ranges from -1 to +1,
    the maximum possible distance is 2.
    Therefore alignment ranges from 0 to 1.
    """

    country_a = country_a.strip().upper()
    country_b = country_b.strip().upper()

    if not country_a or not country_b:
        raise ValueError(
            "Both country codes are required."
        )

    if country_a == country_b:
        raise ValueError(
            "country_a and country_b must be different."
        )

    a = issue_positions(
        con,
        country_code=country_a,
        min_events=min_events,
    )

    b = issue_positions(
        con,
        country_code=country_b,
        min_events=min_events,
    )

    if a.empty or b.empty:
        return pd.DataFrame()

    a = a[
        [
            "issue",
            "year",
            "position_score",
        ]
    ].rename(
        columns={
            "position_score": "score_a",
        }
    )

    b = b[
        [
            "issue",
            "year",
            "position_score",
        ]
    ].rename(
        columns={
            "position_score": "score_b",
        }
    )

    merged = a.merge(
        b,
        on=["issue", "year"],
        how="inner",
    )

    if merged.empty:
        return merged

    merged["absolute_divergence"] = (
        merged["score_a"] - merged["score_b"]
    ).abs()

    merged["alignment_score"] = (
        1.0
        - merged["absolute_divergence"] / 2.0
    )

    merged["directional_agreement"] = (
        (
            merged["score_a"] * merged["score_b"]
        ) > 0
    ).astype(int)

    merged["country_a"] = country_a
    merged["country_b"] = country_b

    return merged[
        [
            "country_a",
            "country_b",
            "issue",
            "year",
            "score_a",
            "score_b",
            "absolute_divergence",
            "alignment_score",
            "directional_agreement",
        ]
    ].sort_values(
        [
            "issue",
            "year",
        ]
    ).reset_index(drop=True)