"""
Coalition intelligence for UN voting data.

Identifies:
- strong voting relationships
- coalition candidates
- temporal coalition changes
- swing states
- bridge states

This module is analytical rather than visual.
"""

from __future__ import annotations

import duckdb
import pandas as pd
import numpy as np


def country_agreement_matrix(
    con: duckdb.DuckDBPyConnection,
    min_common_votes: int = 20,
) -> pd.DataFrame:
    """
    Build the country-pair voting agreement matrix.

    Only Y/N votes are used so that abstentions and absences
    do not artificially create agreement.
    """

    if min_common_votes < 1:
        raise ValueError(
            "min_common_votes must be >= 1"
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

        ORDER BY agreement_percentage DESC
    """

    return con.execute(
        query,
        [min_common_votes],
    ).df()


def strongest_coalitions(
    con: duckdb.DuckDBPyConnection,
    min_common_votes: int = 100,
    min_agreement: float = 75.0,
    limit: int = 50,
) -> pd.DataFrame:
    """
    Return the strongest country-pair coalition relationships.
    """

    if not 0 <= min_agreement <= 100:
        raise ValueError(
            "min_agreement must be between 0 and 100."
        )

    if limit < 1:
        raise ValueError("limit must be >= 1.")

    matrix = country_agreement_matrix(
        con,
        min_common_votes=min_common_votes,
    )

    result = matrix[
        matrix["agreement_percentage"]
        >= min_agreement
    ].copy()

    return (
        result
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


def coalition_profile(
    con: duckdb.DuckDBPyConnection,
    country_code: str,
    min_common_votes: int = 100,
    limit: int = 20,
) -> pd.DataFrame:
    """
    Find the strongest voting relationships for one country.
    """

    country_code = country_code.strip().upper()

    if not country_code:
        raise ValueError(
            "country_code cannot be empty."
        )

    matrix = country_agreement_matrix(
        con,
        min_common_votes=min_common_votes,
    )

    result = matrix[
        (matrix["country_a"] == country_code)
        | (matrix["country_b"] == country_code)
    ].copy()

    result["partner_country"] = np.where(
        result["country_a"] == country_code,
        result["country_b"],
        result["country_a"],
    )

    return (
        result[
            [
                "partner_country",
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


def coalition_trend(
    con: duckdb.DuckDBPyConnection,
    country_a: str,
    country_b: str,
    min_common_votes: int = 5,
) -> pd.DataFrame:
    """
    Calculate year-by-year voting agreement between two countries.

    Only Y/N votes are considered. Abstentions and absences are
    excluded from the agreement calculation.
    """

    country_a = country_a.strip().upper()
    country_b = country_b.strip().upper()

    if not country_a or not country_b:
        raise ValueError(
            "Both country_a and country_b are required."
        )

    if country_a == country_b:
        raise ValueError(
            "country_a and country_b must be different."
        )

    if min_common_votes < 1:
        raise ValueError(
            "min_common_votes must be >= 1."
        )

    query = """
        WITH pair_votes AS (

            SELECT
                d.year,

                a_fact.vote_code AS vote_a,
                b_fact.vote_code AS vote_b

            FROM fact_votes AS a_fact

            JOIN fact_votes AS b_fact
                ON a_fact.vote_event_id =
                   b_fact.vote_event_id

            JOIN dim_country AS a_country
                ON a_fact.country_id =
                   a_country.country_id

            JOIN dim_country AS b_country
                ON b_fact.country_id =
                   b_country.country_id

            JOIN dim_date AS d
                ON a_fact.date_id =
                   d.date_id

            WHERE a_country.ms_code = ?
              AND b_country.ms_code = ?

              AND a_fact.vote_code IN ('Y', 'N')
              AND b_fact.vote_code IN ('Y', 'N')
        )

        SELECT
            year,

            COUNT(*) AS common_votes,

            SUM(
                CASE
                    WHEN vote_a = vote_b
                    THEN 1
                    ELSE 0
                END
            ) AS matching_votes,

            SUM(
                CASE
                    WHEN vote_a != vote_b
                    THEN 1
                    ELSE 0
                END
            ) AS different_votes,

            ROUND(
                SUM(
                    CASE
                        WHEN vote_a = vote_b
                        THEN 1
                        ELSE 0
                    END
                ) * 100.0 / COUNT(*),
                2
            ) AS agreement_percentage

        FROM pair_votes

        GROUP BY year

        HAVING COUNT(*) >= ?

        ORDER BY year
    """

    return con.execute(
        query,
        [
            country_a,
            country_b,
            min_common_votes,
        ],
    ).df()

def coalition_trend_change(
    con: duckdb.DuckDBPyConnection,
    country_a: str,
    country_b: str,
    min_common_votes: int = 5,
) -> pd.DataFrame:
    """
    Quantify whether a bilateral coalition relationship
    is strengthening or weakening over time.
    """

    trend = coalition_trend(
        con,
        country_a,
        country_b,
        min_common_votes,
    )

    if len(trend) < 2:
        return pd.DataFrame(
            columns=[
                "country_a",
                "country_b",
                "first_year",
                "last_year",
                "first_agreement",
                "last_agreement",
                "agreement_change",
                "trend",
            ]
        )

    first = trend.iloc[0]
    last = trend.iloc[-1]

    change = (
        last["agreement_percentage"]
        - first["agreement_percentage"]
    )

    if change > 5:
        direction = "STRENGTHENING"
    elif change < -5:
        direction = "WEAKENING"
    else:
        direction = "STABLE"

    return pd.DataFrame(
        [
            {
                "country_a": country_a.upper(),
                "country_b": country_b.upper(),
                "first_year": int(first["year"]),
                "last_year": int(last["year"]),
                "first_agreement": float(
                    first["agreement_percentage"]
                ),
                "last_agreement": float(
                    last["agreement_percentage"]
                ),
                "agreement_change": round(
                    float(change),
                    2,
                ),
                "trend": direction,
            }
        ]
    )