"""
Temporal coalition intelligence.

Measures how country voting relationships and coalition
membership change across historical time windows.
"""

from __future__ import annotations

import duckdb
import pandas as pd


def build_temporal_network(
    con: duckdb.DuckDBPyConnection,
    start_year: int,
    end_year: int,
    min_common_votes: int = 25,
    min_agreement: float = 75.0,
) -> pd.DataFrame:
    """
    Build a voting network for one historical period.
    """

    if start_year > end_year:
        raise ValueError(
            "start_year must be <= end_year."
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
            start_year,
            end_year,
            min_common_votes,
            min_agreement,
        ],
    ).df()


def extract_coalitions(
    network: pd.DataFrame,
    min_members: int = 3,
) -> list[set[str]]:
    """
    Extract connected coalition candidates from a network.
    """

    adjacency: dict[str, set[str]] = {}

    for row in network.itertuples(index=False):

        a = row.country_a
        b = row.country_b

        adjacency.setdefault(a, set()).add(b)
        adjacency.setdefault(b, set()).add(a)

    visited: set[str] = set()
    coalitions: list[set[str]] = []

    for country in sorted(adjacency):

        if country in visited:
            continue

        stack = [country]
        component: set[str] = set()

        while stack:

            current = stack.pop()

            if current in visited:
                continue

            visited.add(current)
            component.add(current)

            for neighbour in adjacency.get(
                current,
                set(),
            ):
                if neighbour not in visited:
                    stack.append(neighbour)

        if len(component) >= min_members:
            coalitions.append(component)

    return coalitions


def coalition_similarity(
    coalition_a: set[str],
    coalition_b: set[str],
) -> float:
    """
    Calculate Jaccard membership similarity.
    """

    if not coalition_a and not coalition_b:
        return 100.0

    union = coalition_a | coalition_b

    if not union:
        return 0.0

    intersection = coalition_a & coalition_b

    return round(
        len(intersection)
        * 100.0
        / len(union),
        2,
    )


def compare_coalition_periods(
    previous: list[set[str]],
    current: list[set[str]],
) -> pd.DataFrame:
    """
    Match coalitions between consecutive periods.

    The best membership match is selected using Jaccard
    similarity.
    """

    rows = []

    for current_id, current_members in enumerate(
        current,
        start=1,
    ):

        best_similarity = 0.0
        best_previous = None

        for previous_id, previous_members in enumerate(
            previous,
            start=1,
        ):

            similarity = coalition_similarity(
                previous_members,
                current_members,
            )

            if similarity > best_similarity:
                best_similarity = similarity
                best_previous = previous_id

        if best_previous is None:
            trend = "EMERGING"

        elif best_similarity >= 80:
            trend = "STABLE"

        elif best_similarity >= 50:
            trend = "EVOLVING"

        else:
            trend = "NEW_STRUCTURE"

        rows.append(
            {
                "current_coalition_id": current_id,
                "previous_coalition_id": best_previous,
                "membership_similarity": best_similarity,
                "current_member_count": len(
                    current_members
                ),
                "trend": trend,
                "members": ", ".join(
                    sorted(current_members)
                ),
            }
        )

    return pd.DataFrame(rows)


def coalition_membership_changes(
    previous: set[str],
    current: set[str],
) -> dict[str, list[str]]:
    """
    Identify countries entering, leaving, and remaining
    in a coalition.
    """

    return {
        "joined": sorted(
            current - previous
        ),
        "left": sorted(
            previous - current
        ),
        "retained": sorted(
            previous & current
        ),
    }


def temporal_coalition_report(
    con: duckdb.DuckDBPyConnection,
    periods: list[tuple[int, int]],
    min_common_votes: int = 25,
    min_agreement: float = 75.0,
    min_members: int = 3,
) -> pd.DataFrame:
    """
    Produce a complete temporal coalition report.
    """

    period_coalitions = []

    for start_year, end_year in periods:

        network = build_temporal_network(
            con,
            start_year,
            end_year,
            min_common_votes,
            min_agreement,
        )

        coalitions = extract_coalitions(
            network,
            min_members,
        )

        period_coalitions.append(
            (
                (start_year, end_year),
                coalitions,
            )
        )

    rows = []

    for index, (
        period,
        coalitions,
    ) in enumerate(period_coalitions):

        start_year, end_year = period

        if index == 0:

            for coalition_id, members in enumerate(
                coalitions,
                start=1,
            ):
                rows.append(
                    {
                        "period_start": start_year,
                        "period_end": end_year,
                        "coalition_id": coalition_id,
                        "previous_coalition_id": None,
                        "membership_similarity": None,
                        "member_count": len(members),
                        "trend": "BASELINE",
                        "members": ", ".join(
                            sorted(members)
                        ),
                    }
                )

            continue

        previous_coalitions = (
            period_coalitions[index - 1][1]
        )

        comparison = compare_coalition_periods(
            previous_coalitions,
            coalitions,
        )

        for row in comparison.to_dict(
            orient="records"
        ):
            rows.append(
                {
                    "period_start": start_year,
                    "period_end": end_year,
                    "coalition_id": row[
                        "current_coalition_id"
                    ],
                    "previous_coalition_id": row[
                        "previous_coalition_id"
                    ],
                    "membership_similarity": row[
                        "membership_similarity"
                    ],
                    "member_count": row[
                        "current_member_count"
                    ],
                    "trend": row["trend"],
                    "members": row["members"],
                }
            )

    return pd.DataFrame(rows)