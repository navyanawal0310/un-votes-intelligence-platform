"""
Issue-level country position analytics.

Builds country × issue × year voting positions from the
UN General Assembly warehouse.

Position encoding:
    YES     = +1
    ABSTAIN =  0
    NO      = -1

ABSENT votes are excluded from the substantive position score.

This module intentionally preserves the official UN subject labels.
Issue taxonomy/grouping is a later analytical layer.
"""

from __future__ import annotations

import duckdb
import pandas as pd


def issue_positions(
    con: duckdb.DuckDBPyConnection,
    country_code: str,
    min_events: int = 3,
) -> pd.DataFrame:
    """
    Calculate a country's yearly position on each UN subject.

    Parameters
    ----------
    con:
        Active DuckDB connection.

    country_code:
        Official UN Member State code, e.g. IND.

    min_events:
        Minimum number of substantive voting events required
        for an issue/year observation to be returned.

    Returns
    -------
    pandas.DataFrame
        Columns:

        country_code
        issue
        year
        voting_events
        yes_votes
        no_votes
        abstain_votes
        position_score
        yes_percentage
        no_percentage
        abstain_percentage
    """

    country_code = country_code.strip().upper()

    if not country_code:
        raise ValueError("country_code cannot be empty.")

    if min_events < 1:
        raise ValueError("min_events must be >= 1.")

    query = """
        WITH issue_votes AS (
            SELECT
                c.ms_code AS country_code,
                r.subjects AS issue,
                d.year,
                f.vote_code

            FROM fact_votes f

            JOIN dim_country c
                ON f.country_id = c.country_id

            JOIN dim_resolution r
                ON f.resolution_id = r.resolution_id

            JOIN dim_date d
                ON f.date_id = d.date_id

            WHERE c.ms_code = ?

              AND f.vote_code IN ('Y', 'N', 'A')

              AND r.subjects IS NOT NULL

              AND TRIM(r.subjects) <> ''
        ),

        aggregated AS (
            SELECT
                country_code,
                issue,
                year,

                COUNT(*) AS voting_events,

                SUM(
                    CASE
                        WHEN vote_code = 'Y'
                        THEN 1
                        ELSE 0
                    END
                ) AS yes_votes,

                SUM(
                    CASE
                        WHEN vote_code = 'N'
                        THEN 1
                        ELSE 0
                    END
                ) AS no_votes,

                SUM(
                    CASE
                        WHEN vote_code = 'A'
                        THEN 1
                        ELSE 0
                    END
                ) AS abstain_votes

            FROM issue_votes

            GROUP BY
                country_code,
                issue,
                year
        )

        SELECT
            country_code,
            issue,
            year,
            voting_events,
            yes_votes,
            no_votes,
            abstain_votes,

            ROUND(
                (
                    yes_votes - no_votes
                ) * 1.0 / voting_events,
                4
            ) AS position_score,

            ROUND(
                100.0 * yes_votes / voting_events,
                2
            ) AS yes_percentage,

            ROUND(
                100.0 * no_votes / voting_events,
                2
            ) AS no_percentage,

            ROUND(
                100.0 * abstain_votes / voting_events,
                2
            ) AS abstain_percentage

        FROM aggregated

        WHERE voting_events >= ?

        ORDER BY
            issue,
            year
    """

    return con.execute(
        query,
        [country_code, min_events],
    ).df()


def issue_position_history(
    con: duckdb.DuckDBPyConnection,
    country_code: str,
    issue: str,
    min_events: int = 1,
) -> pd.DataFrame:
    """
    Return the complete yearly position history for one
    country and one issue.

    The issue is matched exactly against the normalized
    subject string stored in dim_resolution.
    """

    country_code = country_code.strip().upper()
    issue = issue.strip()

    if not country_code:
        raise ValueError("country_code cannot be empty.")

    if not issue:
        raise ValueError("issue cannot be empty.")

    if min_events < 1:
        raise ValueError("min_events must be >= 1.")

    query = """
        WITH issue_votes AS (
            SELECT
                c.ms_code AS country_code,
                r.subjects AS issue,
                d.year,
                f.vote_code

            FROM fact_votes f

            JOIN dim_country c
                ON f.country_id = c.country_id

            JOIN dim_resolution r
                ON f.resolution_id = r.resolution_id

            JOIN dim_date d
                ON f.date_id = d.date_id

            WHERE c.ms_code = ?
              AND r.subjects = ?
              AND f.vote_code IN ('Y', 'N', 'A')
        ),

        aggregated AS (
            SELECT
                country_code,
                issue,
                year,

                COUNT(*) AS voting_events,

                SUM(
                    CASE
                        WHEN vote_code = 'Y'
                        THEN 1 ELSE 0
                    END
                ) AS yes_votes,

                SUM(
                    CASE
                        WHEN vote_code = 'N'
                        THEN 1 ELSE 0
                    END
                ) AS no_votes,

                SUM(
                    CASE
                        WHEN vote_code = 'A'
                        THEN 1 ELSE 0
                    END
                ) AS abstain_votes

            FROM issue_votes

            GROUP BY
                country_code,
                issue,
                year
        )

        SELECT
            country_code,
            issue,
            year,
            voting_events,
            yes_votes,
            no_votes,
            abstain_votes,

            ROUND(
                (yes_votes - no_votes) * 1.0
                / voting_events,
                4
            ) AS position_score,

            ROUND(
                100.0 * yes_votes / voting_events,
                2
            ) AS yes_percentage,

            ROUND(
                100.0 * no_votes / voting_events,
                2
            ) AS no_percentage,

            ROUND(
                100.0 * abstain_votes / voting_events,
                2
            ) AS abstain_percentage

        FROM aggregated

        WHERE voting_events >= ?

        ORDER BY year
    """

    return con.execute(
        query,
        [country_code, issue, min_events],
    ).df()


def issue_position_summary(
    con: duckdb.DuckDBPyConnection,
    country_code: str,
    min_events: int = 10,
) -> pd.DataFrame:
    """
    Calculate the long-run position of a country across issues.

    Unlike issue_positions(), this aggregates across all available
    years and is intended for ranking/overview analysis.
    """

    country_code = country_code.strip().upper()

    if not country_code:
        raise ValueError("country_code cannot be empty.")

    if min_events < 1:
        raise ValueError("min_events must be >= 1.")

    query = """
        SELECT
            c.ms_code AS country_code,
            r.subjects AS issue,

            COUNT(*) AS voting_events,

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

            ROUND(
                (
                    SUM(
                        CASE
                            WHEN f.vote_code = 'Y'
                            THEN 1
                            WHEN f.vote_code = 'N'
                            THEN -1
                            ELSE 0
                        END
                    ) * 1.0
                ) / COUNT(*),
                4
            ) AS position_score

        FROM fact_votes f

        JOIN dim_country c
            ON f.country_id = c.country_id

        JOIN dim_resolution r
            ON f.resolution_id = r.resolution_id

        WHERE c.ms_code = ?
          AND f.vote_code IN ('Y', 'N', 'A')
          AND r.subjects IS NOT NULL
          AND TRIM(r.subjects) <> ''

        GROUP BY
            c.ms_code,
            r.subjects

        HAVING COUNT(*) >= ?

        ORDER BY
            position_score DESC
    """

    return con.execute(
        query,
        [country_code, min_events],
    ).df()