"""
Bridge and swing-state intelligence for UN voting.

Bridge analysis identifies countries connecting otherwise
distinct voting communities.

Swing analysis identifies countries whose voting alignment
changes substantially between historical periods.
"""

from __future__ import annotations

import duckdb
import pandas as pd


def build_voting_network(
    con: duckdb.DuckDBPyConnection,
    start_year: int,
    end_year: int,
    min_common_votes: int = 25,
    min_agreement: float = 70.0,
) -> pd.DataFrame:
    """
    Build an undirected country voting network for a period.
    """

    query = """
        WITH votes AS (
            SELECT
                c.ms_code,
                f.vote_event_id,
                f.vote_code
            FROM fact_votes f

            JOIN dim_country c
                ON f.country_id = c.country_id

            JOIN dim_date d
                ON f.date_id = d.date_id

            WHERE
                d.year BETWEEN ? AND ?
                AND f.vote_code IN ('Y', 'N')
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
                ON a.vote_event_id = b.vote_event_id
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
            start_year,
            end_year,
            min_common_votes,
            min_agreement,
        ],
    ).df()


def build_adjacency(
    network: pd.DataFrame,
) -> dict[str, set[str]]:
    """
    Convert the voting network into an adjacency structure.
    """

    adjacency: dict[str, set[str]] = {}

    for row in network.itertuples(index=False):

        a = row.country_a
        b = row.country_b

        adjacency.setdefault(a, set()).add(b)
        adjacency.setdefault(b, set()).add(a)

    return adjacency


def calculate_bridge_scores(
    network: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate a structural bridge score.

    The score is based on how many of a country's
    connections are themselves poorly connected.

    Higher score = stronger potential bridge position.

    This is a structural indicator, not a political claim.
    """

    adjacency = build_adjacency(network)

    rows = []

    for country, neighbours in adjacency.items():

        if len(neighbours) < 2:
            rows.append(
                {
                    "ms_code": country,
                    "degree": len(neighbours),
                    "bridge_score": 0.0,
                }
            )
            continue

        total = 0.0

        for neighbour in neighbours:

            neighbour_connections = adjacency.get(
                neighbour,
                set(),
            )

            if not neighbour_connections:
                continue

            overlap = len(
                neighbours
                & neighbour_connections
            )

            isolation = (
                1.0
                - overlap
                / max(
                    len(neighbours),
                    1,
                )
            )

            total += isolation

        bridge_score = (
            total / len(neighbours)
        ) * 100.0

        rows.append(
            {
                "ms_code": country,
                "degree": len(neighbours),
                "bridge_score": round(
                    bridge_score,
                    2,
                ),
            }
        )

    return (
        pd.DataFrame(rows)
        .sort_values(
            [
                "bridge_score",
                "degree",
            ],
            ascending=False,
        )
        .reset_index(drop=True)
    )


def calculate_alignment_change(
    previous_network: pd.DataFrame,
    current_network: pd.DataFrame,
) -> pd.DataFrame:
    """
    Measure change in each country's average voting
    agreement between two periods.
    """

    def country_agreement(
        network: pd.DataFrame,
    ) -> pd.Series:

        a = network[
            [
                "country_a",
                "agreement_percentage",
            ]
        ].rename(
            columns={
                "country_a": "ms_code"
            }
        )

        b = network[
            [
                "country_b",
                "agreement_percentage",
            ]
        ].rename(
            columns={
                "country_b": "ms_code"
            }
        )

        combined = pd.concat(
            [a, b],
            ignore_index=True,
        )

        return (
            combined
            .groupby("ms_code")[
                "agreement_percentage"
            ]
            .mean()
        )

    previous = country_agreement(
        previous_network
    )

    current = country_agreement(
        current_network
    )

    result = pd.concat(
        [
            previous.rename(
                "previous_agreement"
            ),
            current.rename(
                "current_agreement"
            ),
        ],
        axis=1,
    ).dropna()

    result["alignment_change"] = (
        result["current_agreement"]
        - result["previous_agreement"]
    )

    result["swing_score"] = (
        result["alignment_change"]
        .abs()
        .round(2)
    )

    result["direction"] = (
        result["alignment_change"]
        .apply(
            lambda x:
                "STRENGTHENED"
                if x > 0
                else (
                    "WEAKENED"
                    if x < 0
                    else "STABLE"
                )
        )
    )

    return (
        result
        .reset_index()
        .sort_values(
            "swing_score",
            ascending=False,
        )
    )


def identify_swing_states(
    alignment_changes: pd.DataFrame,
    threshold: float = 10.0,
) -> pd.DataFrame:
    """
    Identify countries whose average alignment
    changed by at least the specified number of
    percentage points.
    """

    return (
        alignment_changes[
            alignment_changes["swing_score"]
            >= threshold
        ]
        .copy()
        .reset_index(drop=True)
    )


def bridge_swing_report(
    con: duckdb.DuckDBPyConnection,
    previous_period: tuple[int, int],
    current_period: tuple[int, int],
    min_common_votes: int = 25,
    min_agreement: float = 70.0,
    swing_threshold: float = 10.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:

    previous_network = build_voting_network(
        con,
        previous_period[0],
        previous_period[1],
        min_common_votes,
        min_agreement,
    )

    current_network = build_voting_network(
        con,
        current_period[0],
        current_period[1],
        min_common_votes,
        min_agreement,
    )

    bridge_scores = calculate_bridge_scores(
        current_network
    )

    alignment_changes = calculate_alignment_change(
        previous_network,
        current_network,
    )

    swing_states = identify_swing_states(
        alignment_changes,
        swing_threshold,
    )

    return bridge_scores, swing_states