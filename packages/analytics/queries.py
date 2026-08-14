"""
Analytical queries for the UN voting warehouse.
"""

from __future__ import annotations

import duckdb
import pandas as pd


def country_voting_profile(
    con: duckdb.DuckDBPyConnection,
) -> pd.DataFrame:
    """
    Return aggregate voting statistics for every Member State.
    """

    return con.execute(
        """
        SELECT
            c.country_id,
            c.ms_code,
            c.country_name,

            COUNT(*) AS total_votes,

            SUM(
                CASE
                    WHEN f.vote_code = 'Y' THEN 1
                    ELSE 0
                END
            ) AS yes_votes,

            SUM(
                CASE
                    WHEN f.vote_code = 'N' THEN 1
                    ELSE 0
                END
            ) AS no_votes,

            SUM(
                CASE
                    WHEN f.vote_code = 'A' THEN 1
                    ELSE 0
                END
            ) AS abstain_votes,

            SUM(
                CASE
                    WHEN f.vote_code = 'X' THEN 1
                    ELSE 0
                END
            ) AS absent_votes,

            ROUND(
                100.0 *
                SUM(
                    CASE
                        WHEN f.vote_code = 'Y' THEN 1
                        ELSE 0
                    END
                )
                / COUNT(*),
                2
            ) AS yes_percentage

        FROM fact_votes f

        JOIN dim_country c
            ON f.country_id = c.country_id

        GROUP BY
            c.country_id,
            c.ms_code,
            c.country_name

        ORDER BY
            yes_percentage DESC,
            c.country_name
        """
    ).df()

def country_voting_similarity(
    con: duckdb.DuckDBPyConnection,
    country_a: str,
    country_b: str,
) -> pd.DataFrame:
    """
    Compare voting agreement between two Member States.

    Agreement is calculated only across voting events where
    both countries have a recorded vote.
    """

    return con.execute(
        """
        WITH country_a_votes AS (
            SELECT
                f.vote_event_id,
                f.vote_code AS vote_a
            FROM fact_votes f
            JOIN dim_country c
                ON f.country_id = c.country_id
            WHERE c.ms_code = ?
        ),

        country_b_votes AS (
            SELECT
                f.vote_event_id,
                f.vote_code AS vote_b
            FROM fact_votes f
            JOIN dim_country c
                ON f.country_id = c.country_id
            WHERE c.ms_code = ?
        ),

        comparison AS (
            SELECT
                a.vote_event_id,
                a.vote_a,
                b.vote_b,
                CASE
                    WHEN a.vote_a = b.vote_b THEN 1
                    ELSE 0
                END AS agreement
            FROM country_a_votes a
            INNER JOIN country_b_votes b
                ON a.vote_event_id = b.vote_event_id
        )

        SELECT
            ? AS country_a,
            ? AS country_b,

            COUNT(*) AS common_voting_events,

            SUM(agreement) AS matching_votes,

            COUNT(*) - SUM(agreement)
                AS different_votes,

            ROUND(
                100.0 * SUM(agreement) / COUNT(*),
                2
            ) AS agreement_percentage

        FROM comparison
        """,
        [
            country_a,
            country_b,
            country_a,
            country_b,
        ],
    ).df()
    
def rank_country_similarity(
    con: duckdb.DuckDBPyConnection,
    country_code: str,
) -> pd.DataFrame:
    """
    Rank all other Member States by voting similarity
    to the selected country.

    Similarity is calculated using only voting events where
    both countries have a recorded vote.
    """

    return con.execute(
        """
        WITH target_votes AS (
            SELECT
                f.vote_event_id,
                f.vote_code AS target_vote
            FROM fact_votes f
            JOIN dim_country c
                ON f.country_id = c.country_id
            WHERE c.ms_code = ?
        ),

        other_votes AS (
            SELECT
                f.vote_event_id,
                c.ms_code,
                c.country_name,
                f.vote_code AS other_vote
            FROM fact_votes f
            JOIN dim_country c
                ON f.country_id = c.country_id
            WHERE c.ms_code != ?
        ),

        comparison AS (
            SELECT
                o.ms_code,
                o.country_name,
                o.vote_event_id,

                CASE
                    WHEN t.target_vote = o.other_vote
                    THEN 1
                    ELSE 0
                END AS agreement

            FROM other_votes o

            INNER JOIN target_votes t
                ON o.vote_event_id = t.vote_event_id
        )

        SELECT
            ms_code,
            country_name,

            COUNT(*) AS common_voting_events,

            SUM(agreement) AS matching_votes,

            COUNT(*) - SUM(agreement)
                AS different_votes,

            ROUND(
                100.0 * SUM(agreement) / COUNT(*),
                2
            ) AS agreement_percentage

        FROM comparison

        GROUP BY
            ms_code,
            country_name

        ORDER BY
            agreement_percentage DESC,
            common_voting_events DESC,
            country_name
        """,
        [
            country_code,
            country_code,
        ],
    ).df()

def country_similarity_by_year(
    con: duckdb.DuckDBPyConnection,
    country_a: str,
    country_b: str,
) -> pd.DataFrame:
    """
    Calculate voting similarity between two countries by year.

    Similarity is calculated only for voting events where both
    countries have a recorded vote.
    """

    return con.execute(
        """
        WITH country_a_votes AS (
            SELECT
                f.vote_event_id,
                d.year,
                f.vote_code AS vote_a
            FROM fact_votes f
            JOIN dim_country c
                ON f.country_id = c.country_id
            JOIN dim_date d
                ON f.date_id = d.date_id
            WHERE c.ms_code = ?
        ),

        country_b_votes AS (
            SELECT
                f.vote_event_id,
                d.year,
                f.vote_code AS vote_b
            FROM fact_votes f
            JOIN dim_country c
                ON f.country_id = c.country_id
            JOIN dim_date d
                ON f.date_id = d.date_id
            WHERE c.ms_code = ?
        ),

        comparison AS (
            SELECT
                a.year,
                a.vote_event_id,
                a.vote_a,
                b.vote_b,

                CASE
                    WHEN a.vote_a = b.vote_b
                    THEN 1
                    ELSE 0
                END AS agreement

            FROM country_a_votes a

            INNER JOIN country_b_votes b
                ON a.vote_event_id = b.vote_event_id
        )

        SELECT
            ? AS country_a,
            ? AS country_b,
            year,

            COUNT(*) AS common_voting_events,

            SUM(agreement) AS matching_votes,

            COUNT(*) - SUM(agreement)
                AS different_votes,

            ROUND(
                100.0 * SUM(agreement) / COUNT(*),
                2
            ) AS agreement_percentage

        FROM comparison

        GROUP BY
            year

        ORDER BY
            year
        """,
        [
            country_a,
            country_b,
            country_a,
            country_b,
        ],
    ).df()

def country_substantive_similarity_by_year(
    con: duckdb.DuckDBPyConnection,
    country_a: str,
    country_b: str,
    min_common_events: int = 20,
) -> pd.DataFrame:
    """
    Calculate substantive voting similarity between two countries
    by year.

    ABSENT votes are excluded.

    Years with fewer than min_common_events common substantive
    votes are excluded from the result.
    """

    return con.execute(
        """
        WITH country_a_votes AS (
            SELECT
                f.vote_event_id,
                d.year,
                f.vote_code AS vote_a
            FROM fact_votes f
            JOIN dim_country c
                ON f.country_id = c.country_id
            JOIN dim_date d
                ON f.date_id = d.date_id
            WHERE c.ms_code = ?
              AND f.vote_code IN ('Y', 'N', 'A')
        ),

        country_b_votes AS (
            SELECT
                f.vote_event_id,
                d.year,
                f.vote_code AS vote_b
            FROM fact_votes f
            JOIN dim_country c
                ON f.country_id = c.country_id
            JOIN dim_date d
                ON f.date_id = d.date_id
            WHERE c.ms_code = ?
              AND f.vote_code IN ('Y', 'N', 'A')
        ),

        comparison AS (
            SELECT
                a.year,
                a.vote_event_id,

                CASE
                    WHEN a.vote_a = b.vote_b
                    THEN 1
                    ELSE 0
                END AS agreement

            FROM country_a_votes a

            INNER JOIN country_b_votes b
                ON a.vote_event_id = b.vote_event_id
        )

        SELECT
            ? AS country_a,
            ? AS country_b,
            year,

            COUNT(*) AS common_substantive_votes,

            SUM(agreement) AS matching_votes,

            COUNT(*) - SUM(agreement)
                AS different_votes,

            ROUND(
                100.0 * SUM(agreement) / COUNT(*),
                2
            ) AS agreement_percentage

        FROM comparison

        GROUP BY year

        HAVING COUNT(*) >= ?

        ORDER BY year
        """,
        [
            country_a,
            country_b,
            country_a,
            country_b,
            min_common_events,
        ],
    ).df()