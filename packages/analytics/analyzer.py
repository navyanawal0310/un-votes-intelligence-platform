"""
High-level analytical interface for the UN Votes Analyzer.
"""

from __future__ import annotations

import duckdb
import pandas as pd

from packages.analytics.queries import (
    country_voting_profile,
    rank_country_similarity,
    country_similarity_by_year,
    country_substantive_similarity_by_year,
)


def analyze_country(
    con: duckdb.DuckDBPyConnection,
    ms_code: str,
    top_n: int = 20,
) -> dict[str, pd.DataFrame]:
    """
    Produce a complete analytical profile for a country.

    Parameters
    ----------
    con:
        Active DuckDB connection.

    ms_code:
        UN Member State code, e.g. "IND".

    top_n:
        Number of similar countries to return.

    Returns
    -------
    dict[str, pd.DataFrame]
        Collection of analytical outputs.
    """

    ms_code = ms_code.strip().upper()

    # ---------------------------------------------------------
    # 1. Country voting profile
    # ---------------------------------------------------------

    profile = country_voting_profile(con)
    profile = (
        profile[
            profile["ms_code"] == ms_code
        ]
        .reset_index(drop=True)
    )
    if profile.empty:
        raise ValueError(
            f"Country not found in warehouse: {ms_code}"
        )
    # ---------------------------------------------------------
    # 2. Country similarity ranking
    # ---------------------------------------------------------

    similarity = rank_country_similarity(
        con,
        ms_code,
    )

    similarity = similarity.head(top_n).reset_index(drop=True)

    # ---------------------------------------------------------
    # 3. Historical similarity
    # ---------------------------------------------------------

    yearly_similarity = country_similarity_by_year(
        con,
        ms_code,
        "CHN",
    )

    # ---------------------------------------------------------
    # 4. Substantive historical similarity
    # ---------------------------------------------------------

    substantive_yearly_similarity = (
        country_substantive_similarity_by_year(
            con,
            ms_code,
            "CHN",
            min_common_events=20,
        )
    )

    return {
        "profile": profile,
        "similar_countries": similarity,
        "yearly_similarity": yearly_similarity,
        "substantive_yearly_similarity":
            substantive_yearly_similarity,
    }
def compare_countries(
    con: duckdb.DuckDBPyConnection,
    country_a: str,
    country_b: str,
    min_common_events: int = 20,
) -> dict[str, pd.DataFrame]:
    """
    Compare two UN Member States across voting history.

    Returns:
        profile_a
        profile_b
        yearly_similarity
        substantive_yearly_similarity
    """

    country_a = country_a.strip().upper()
    country_b = country_b.strip().upper()

    if country_a == country_b:
        raise ValueError(
            "country_a and country_b must be different."
        )

    # ---------------------------------------------------------
    # Country profiles
    # ---------------------------------------------------------

    profiles = country_voting_profile(con)

    profile_a = (
        profiles[
            profiles["ms_code"] == country_a
        ]
        .reset_index(drop=True)
    )

    profile_b = (
        profiles[
            profiles["ms_code"] == country_b
        ]
        .reset_index(drop=True)
    )

    if profile_a.empty:
        raise ValueError(
            f"Country not found: {country_a}"
        )

    if profile_b.empty:
        raise ValueError(
            f"Country not found: {country_b}"
        )

    # ---------------------------------------------------------
    # Overall voting similarity
    # ---------------------------------------------------------

    similarity = rank_country_similarity(
        con,
        country_a,
    )

    pair_similarity = similarity[
        similarity["ms_code"] == country_b
    ].reset_index(drop=True)

    # ---------------------------------------------------------
    # Yearly similarity
    # ---------------------------------------------------------

    yearly_similarity = country_similarity_by_year(
        con,
        country_a,
        country_b,
    )

    # ---------------------------------------------------------
    # Substantive yearly similarity
    # ---------------------------------------------------------

    substantive_yearly_similarity = (
        country_substantive_similarity_by_year(
            con,
            country_a,
            country_b,
            min_common_events=min_common_events,
        )
    )

    return {
        "profile_a": profile_a,
        "profile_b": profile_b,
        "similarity": pair_similarity,
        "yearly_similarity": yearly_similarity,
        "substantive_yearly_similarity":
            substantive_yearly_similarity,
    }