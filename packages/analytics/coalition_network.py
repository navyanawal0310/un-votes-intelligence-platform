"""
Multi-country coalition network analysis.

Builds a weighted voting network from country-pair agreement
and identifies coalition communities and structurally important
countries.

This module is analytical and does not perform visualization.
"""

from __future__ import annotations

import duckdb
import pandas as pd
import numpy as np


def build_voting_network(
    con: duckdb.DuckDBPyConnection,
    min_common_votes: int = 100,
    min_agreement: float = 75.0,
) -> pd.DataFrame:
    """
    Build the weighted country voting network.

    Each row represents an edge between two countries.

    Edge weight:
        voting agreement percentage.

    Only relationships satisfying the minimum number of
    common votes and minimum agreement are retained.
    """

    if min_common_votes < 1:
        raise ValueError(
            "min_common_votes must be >= 1."
        )

    if not 0 <= min_agreement <= 100:
        raise ValueError(
            "min_agreement must be between 0 and 100."
        )

    query = """
        WITH votes AS (

            SELECT
                c.ms_code,
                f.vote_event_id,
                f.vote_code

            FROM fact_votes f

            JOIN dim_country c
                ON f.country_id = c.country_id

            WHERE f.vote_code IN ('Y', 'N')
        ),

        pairs AS (

            SELECT
                a.ms_code AS country_a,
                b.ms_code AS country_b,

                COUNT(*) AS common_votes,

                SUM(
                    CASE
                        WHEN a.vote_code = b.vote_code
                        THEN 1
                        ELSE 0
                    END
                ) AS matching_votes

            FROM votes a

            JOIN votes b
                ON a.vote_event_id =
                   b.vote_event_id

               AND a.ms_code < b.ms_code

            GROUP BY
                a.ms_code,
                b.ms_code

            HAVING COUNT(*) >= ?
        )

        SELECT
            country_a,
            country_b,
            common_votes,
            matching_votes,

            common_votes - matching_votes
                AS different_votes,

            ROUND(
                matching_votes * 100.0
                / NULLIF(common_votes, 0),
                2
            ) AS agreement_percentage

        FROM pairs

        WHERE
            matching_votes * 100.0
            / NULLIF(common_votes, 0)
            >= ?

        ORDER BY agreement_percentage DESC
    """

    return con.execute(
        query,
        [
            min_common_votes,
            min_agreement,
        ],
    ).df()


def network_summary(
    network: pd.DataFrame,
) -> pd.DataFrame:
    """
    Produce basic structural statistics for the voting network.
    """

    required = {
        "country_a",
        "country_b",
        "agreement_percentage",
    }

    missing = required - set(network.columns)

    if missing:
        raise ValueError(
            f"Missing network columns: {sorted(missing)}"
        )

    countries = set(network["country_a"])
    countries.update(network["country_b"])

    return pd.DataFrame(
        [
            {
                "countries": len(countries),
                "edges": len(network),
                "mean_agreement": round(
                    network[
                        "agreement_percentage"
                    ].mean(),
                    2,
                ),
                "median_agreement": round(
                    network[
                        "agreement_percentage"
                    ].median(),
                    2,
                ),
                "min_agreement": round(
                    network[
                        "agreement_percentage"
                    ].min(),
                    2,
                ),
                "max_agreement": round(
                    network[
                        "agreement_percentage"
                    ].max(),
                    2,
                ),
            }
        ]
    )


def country_network_strength(
    network: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate weighted network strength for every country.

    Strength is the sum of agreement weights across
    all retained relationships.
    """

    a = (
        network[
            [
                "country_a",
                "agreement_percentage",
            ]
        ]
        .rename(
            columns={
                "country_a": "country"
            }
        )
    )

    b = (
        network[
            [
                "country_b",
                "agreement_percentage",
            ]
        ]
        .rename(
            columns={
                "country_b": "country"
            }
        )
    )

    result = (
        pd.concat([a, b])
        .groupby("country", as_index=False)
        .agg(
            network_strength=(
                "agreement_percentage",
                "sum",
            ),
            coalition_connections=(
                "agreement_percentage",
                "count",
            ),
        )
        .sort_values(
            "network_strength",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    return result


def strongest_network_partners(
    network: pd.DataFrame,
    country_code: str,
    limit: int = 20,
) -> pd.DataFrame:
    """
    Return strongest network relationships for a country.
    """

    country_code = country_code.strip().upper()

    if not country_code:
        raise ValueError(
            "country_code cannot be empty."
        )

    if limit < 1:
        raise ValueError(
            "limit must be >= 1."
        )

    result_a = (
        network[
            network["country_a"] == country_code
        ]
        .copy()
    )

    result_a["partner"] = result_a["country_b"]

    result_b = (
        network[
            network["country_b"] == country_code
        ]
        .copy()
    )

    result_b["partner"] = result_b["country_a"]

    result = pd.concat(
        [
            result_a,
            result_b,
        ],
        ignore_index=True,
    )

    return (
        result[
            [
                "partner",
                "common_votes",
                "matching_votes",
                "different_votes",
                "agreement_percentage",
            ]
        ]
        .sort_values(
            [
                "agreement_percentage",
                "common_votes",
            ],
            ascending=[False, False],
        )
        .head(limit)
        .reset_index(drop=True)
    )


def detect_coalition_candidates(
    network: pd.DataFrame,
    min_members: int = 3,
    min_internal_agreement: float = 80.0,
) -> pd.DataFrame:
    """
    Detect simple coalition candidates using connected
    components in the high-agreement voting network.

    This is deliberately the first network layer.

    Later we will replace/augment this with formal community
    detection and temporal coalition analysis.
    """

    if min_members < 2:
        raise ValueError(
            "min_members must be >= 2."
        )

    if not 0 <= min_internal_agreement <= 100:
        raise ValueError(
            "min_internal_agreement must be between 0 and 100."
        )

    filtered = network[
        network["agreement_percentage"]
        >= min_internal_agreement
    ].copy()

    adjacency: dict[str, set[str]] = {}

    for row in filtered.itertuples(index=False):

        a = row.country_a
        b = row.country_b

        adjacency.setdefault(a, set()).add(b)
        adjacency.setdefault(b, set()).add(a)

    visited: set[str] = set()
    communities: list[list[str]] = []

    for country in sorted(adjacency):

        if country in visited:
            continue

        stack = [country]
        component = []

        while stack:

            current = stack.pop()

            if current in visited:
                continue

            visited.add(current)
            component.append(current)

            for neighbour in adjacency.get(
                current,
                set(),
            ):
                if neighbour not in visited:
                    stack.append(neighbour)

        if len(component) >= min_members:
            communities.append(
                sorted(component)
            )

    rows = []

    for coalition_id, members in enumerate(
        communities,
        start=1,
    ):

        rows.append(
            {
                "coalition_id": coalition_id,
                "member_count": len(members),
                "members": ", ".join(members),
            }
        )

    return (
        pd.DataFrame(rows)
        .sort_values(
            "member_count",
            ascending=False,
        )
        .reset_index(drop=True)
        if rows
        else pd.DataFrame(
            columns=[
                "coalition_id",
                "member_count",
                "members",
            ]
        )
    )