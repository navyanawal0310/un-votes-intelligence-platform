"""
Time-series analytics for the UN Votes Intelligence Platform.

Provides reusable yearly voting-alignment metrics for:
    - country vs country
    - country vs bloc
    - country voting behavior

The module contains analytics only. No frontend/API logic belongs here.
"""

from __future__ import annotations

import duckdb
import pandas as pd


VALID_VOTES = ("Y", "N", "A", "X")


def country_agreement_timeline(
    con: duckdb.DuckDBPyConnection,
    country_a: str,
    country_b: str,
) -> pd.DataFrame:
    """
    Calculate yearly voting agreement between two countries.

    Agreement is based on exact vote-code matches.

    Returns:
        year
        common_voting_events
        matching_votes
        different_votes
        agreement_percentage
        disagreement_percentage
    """

    country_a = country_a.strip().upper()
    country_b = country_b.strip().upper()

    if not country_a or not country_b:
        raise ValueError("Country codes cannot be empty.")

    if country_a == country_b:
        raise ValueError("country_a and country_b must be different.")

    query = """
        WITH country_a_votes AS (
            SELECT
                f.vote_event_id,
                d.year,
                f.vote_code
            FROM fact_votes f
            JOIN dim_country c
                ON f.country_id = c.country_id
            JOIN dim_date d
                ON f.date_id = d.date_id
            WHERE c.ms_code = ?
              AND f.vote_code IN ('Y', 'N', 'A', 'X')
        ),

        country_b_votes AS (
            SELECT
                f.vote_event_id,
                f.vote_code
            FROM fact_votes f
            JOIN dim_country c
                ON f.country_id = c.country_id
            WHERE c.ms_code = ?
              AND f.vote_code IN ('Y', 'N', 'A', 'X')
        )

        SELECT
            a.year,

            COUNT(*) AS common_voting_events,

            SUM(
                CASE
                    WHEN a.vote_code = b.vote_code
                    THEN 1
                    ELSE 0
                END
            ) AS matching_votes,

            SUM(
                CASE
                    WHEN a.vote_code <> b.vote_code
                    THEN 1
                    ELSE 0
                END
            ) AS different_votes,

            ROUND(
                100.0 *
                SUM(
                    CASE
                        WHEN a.vote_code = b.vote_code
                        THEN 1
                        ELSE 0
                    END
                ) / COUNT(*),
                2
            ) AS agreement_percentage,

            ROUND(
                100.0 *
                SUM(
                    CASE
                        WHEN a.vote_code <> b.vote_code
                        THEN 1
                        ELSE 0
                    END
                ) / COUNT(*),
                2
            ) AS disagreement_percentage

        FROM country_a_votes a

        JOIN country_b_votes b
            ON a.vote_event_id = b.vote_event_id

        GROUP BY a.year

        ORDER BY a.year
    """

    return con.execute(
        query,
        [country_a, country_b],
    ).df()


def country_vote_timeline(
    con: duckdb.DuckDBPyConnection,
    country_code: str,
) -> pd.DataFrame:
    """
    Calculate a country's yearly voting behavior.

    Returns:
        year
        total_votes
        yes_votes
        no_votes
        abstain_votes
        absent_votes
        yes_percentage
        no_percentage
        abstain_percentage
        absent_percentage
    """

    country_code = country_code.strip().upper()

    if not country_code:
        raise ValueError("country_code cannot be empty.")

    query = """
        SELECT
            d.year,

            COUNT(*) AS total_votes,

            SUM(
                CASE WHEN f.vote_code = 'Y'
                THEN 1 ELSE 0 END
            ) AS yes_votes,

            SUM(
                CASE WHEN f.vote_code = 'N'
                THEN 1 ELSE 0 END
            ) AS no_votes,

            SUM(
                CASE WHEN f.vote_code = 'A'
                THEN 1 ELSE 0 END
            ) AS abstain_votes,

            SUM(
                CASE WHEN f.vote_code = 'X'
                THEN 1 ELSE 0 END
            ) AS absent_votes,

            ROUND(
                100.0 *
                SUM(CASE WHEN f.vote_code = 'Y' THEN 1 ELSE 0 END)
                / COUNT(*),
                2
            ) AS yes_percentage,

            ROUND(
                100.0 *
                SUM(CASE WHEN f.vote_code = 'N' THEN 1 ELSE 0 END)
                / COUNT(*),
                2
            ) AS no_percentage,

            ROUND(
                100.0 *
                SUM(CASE WHEN f.vote_code = 'A' THEN 1 ELSE 0 END)
                / COUNT(*),
                2
            ) AS abstain_percentage,

            ROUND(
                100.0 *
                SUM(CASE WHEN f.vote_code = 'X' THEN 1 ELSE 0 END)
                / COUNT(*),
                2
            ) AS absent_percentage

        FROM fact_votes f

        JOIN dim_country c
            ON f.country_id = c.country_id

        JOIN dim_date d
            ON f.date_id = d.date_id

        WHERE c.ms_code = ?

        GROUP BY d.year

        ORDER BY d.year
    """

    return con.execute(
        query,
        [country_code],
    ).df()


def bloc_agreement_timeline(
    con: duckdb.DuckDBPyConnection,
    country_code: str,
    bloc_codes: list[str],
) -> pd.DataFrame:
    """
    Calculate yearly agreement between a country and
    the majority voting position of a bloc.

    The bloc position for each voting event is determined
    by the majority vote among bloc members.

    Returns:
        year
        common_voting_events
        matching_votes
        different_votes
        agreement_percentage
        disagreement_percentage
    """

    country_code = country_code.strip().upper()

    bloc_codes = [
        code.strip().upper()
        for code in bloc_codes
        if code and code.strip()
    ]

    bloc_codes = [
        code
        for code in bloc_codes
        if code != country_code
    ]

    if not country_code:
        raise ValueError("country_code cannot be empty.")

    if not bloc_codes:
        raise ValueError(
            "bloc_codes must contain at least one other country."
        )

    placeholders = ", ".join("?" for _ in bloc_codes)

    query = f"""
        WITH target_votes AS (
            SELECT
                f.vote_event_id,
                d.year,
                f.vote_code AS target_vote
            FROM fact_votes f
            JOIN dim_country c
                ON f.country_id = c.country_id
            JOIN dim_date d
                ON f.date_id = d.date_id
            WHERE c.ms_code = ?
              AND f.vote_code IN ('Y', 'N', 'A')
        ),

        bloc_votes AS (
            SELECT
                f.vote_event_id,
                f.vote_code
            FROM fact_votes f
            JOIN dim_country c
                ON f.country_id = c.country_id
            WHERE c.ms_code IN ({placeholders})
              AND f.vote_code IN ('Y', 'N', 'A')
        ),

        bloc_counts AS (
            SELECT
                vote_event_id,

                SUM(
                    CASE WHEN vote_code = 'Y'
                    THEN 1 ELSE 0 END
                ) AS yes_count,

                SUM(
                    CASE WHEN vote_code = 'N'
                    THEN 1 ELSE 0 END
                ) AS no_count,

                SUM(
                    CASE WHEN vote_code = 'A'
                    THEN 1 ELSE 0 END
                ) AS abstain_count

            FROM bloc_votes

            GROUP BY vote_event_id
        ),

        bloc_majority AS (
            SELECT
                vote_event_id,

                CASE
                    WHEN yes_count >= no_count
                         AND yes_count >= abstain_count
                        THEN 'Y'

                    WHEN no_count >= yes_count
                         AND no_count >= abstain_count
                        THEN 'N'

                    ELSE 'A'
                END AS bloc_vote

            FROM bloc_counts
        )

        SELECT
            t.year,

            COUNT(*) AS common_voting_events,

            SUM(
                CASE
                    WHEN t.target_vote = b.bloc_vote
                    THEN 1
                    ELSE 0
                END
            ) AS matching_votes,

            SUM(
                CASE
                    WHEN t.target_vote <> b.bloc_vote
                    THEN 1
                    ELSE 0
                END
            ) AS different_votes,

            ROUND(
                100.0 *
                SUM(
                    CASE
                        WHEN t.target_vote = b.bloc_vote
                        THEN 1
                        ELSE 0
                    END
                ) / COUNT(*),
                2
            ) AS agreement_percentage,

            ROUND(
                100.0 *
                SUM(
                    CASE
                        WHEN t.target_vote <> b.bloc_vote
                        THEN 1
                        ELSE 0
                    END
                ) / COUNT(*),
                2
            ) AS disagreement_percentage

        FROM target_votes t

        JOIN bloc_majority b
            ON t.vote_event_id = b.vote_event_id

        GROUP BY t.year

        ORDER BY t.year
    """

    params = [country_code] + bloc_codes

    return con.execute(query, params).df()