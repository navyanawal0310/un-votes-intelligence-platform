"""
Bloc-level voting analysis for the UN Votes Intelligence platform.

Provides analysis of how one country votes compared with a
defined group (bloc) of countries.
"""

from __future__ import annotations

import duckdb
import pandas as pd


SUBSTANTIVE_CODES = ("Y", "N", "A")


def bloc_voting_profile(
    con: duckdb.DuckDBPyConnection,
    country_code: str,
    bloc_codes: list[str],
) -> pd.DataFrame:
    """
    Compare a country's substantive votes with the collective
    voting behavior of a defined bloc.

    For each voting event, the bloc's majority vote is calculated.
    The target country's vote is then compared against that majority.

    Returns:
        vote_code
        bloc_majority_vote
        voting_events
        matching_events
        different_events
        agreement_percentage
    """

    if not country_code:
        raise ValueError("country_code cannot be empty.")

    if not bloc_codes:
        raise ValueError("bloc_codes cannot be empty.")

    bloc_codes = [
        code.strip().upper()
        for code in bloc_codes
        if code and code.strip()
    ]

    country_code = country_code.strip().upper()

    if country_code in bloc_codes:
        bloc_codes = [
            code for code in bloc_codes
            if code != country_code
        ]

    if not bloc_codes:
        raise ValueError(
            "Bloc must contain at least one country "
            "different from the target country."
        )

    placeholders = ", ".join("?" for _ in bloc_codes)

    query = f"""
        WITH target_votes AS (
            SELECT
                f.vote_event_id,
                f.vote_code AS target_vote
            FROM fact_votes f
            JOIN dim_country c
                ON f.country_id = c.country_id
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
                END AS bloc_majority_vote

            FROM bloc_counts
        )

        SELECT
            t.target_vote AS vote_code,
            b.bloc_majority_vote,

            COUNT(*) AS voting_events,

            SUM(
                CASE
                    WHEN t.target_vote = b.bloc_majority_vote
                    THEN 1
                    ELSE 0
                END
            ) AS matching_events,

            SUM(
                CASE
                    WHEN t.target_vote <> b.bloc_majority_vote
                    THEN 1
                    ELSE 0
                END
            ) AS different_events,

            ROUND(
                100.0 *
                SUM(
                    CASE
                        WHEN t.target_vote = b.bloc_majority_vote
                        THEN 1
                        ELSE 0
                    END
                )
                / COUNT(*),
                2
            ) AS agreement_percentage

        FROM target_votes t

        JOIN bloc_majority b
            ON t.vote_event_id = b.vote_event_id

        GROUP BY
            t.target_vote,
            b.bloc_majority_vote

        ORDER BY
            t.target_vote,
            b.bloc_majority_vote
    """

    params = [country_code] + bloc_codes

    return con.execute(query, params).df()


def country_vs_bloc(
    con: duckdb.DuckDBPyConnection,
    country_code: str,
    bloc_codes: list[str],
) -> pd.DataFrame:
    """
    Calculate overall voting agreement between one country
    and the majority position of a bloc.
    """

    if not country_code:
        raise ValueError("country_code cannot be empty.")

    if not bloc_codes:
        raise ValueError("bloc_codes cannot be empty.")

    bloc_codes = [
        code.strip().upper()
        for code in bloc_codes
        if code and code.strip()
    ]

    country_code = country_code.strip().upper()

    bloc_codes = [
        code for code in bloc_codes
        if code != country_code
    ]

    placeholders = ", ".join("?" for _ in bloc_codes)

    query = f"""
        WITH target_votes AS (
            SELECT
                f.vote_event_id,
                f.vote_code AS target_vote
            FROM fact_votes f
            JOIN dim_country c
                ON f.country_id = c.country_id
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

                SUM(CASE WHEN vote_code = 'Y' THEN 1 ELSE 0 END)
                    AS yes_count,

                SUM(CASE WHEN vote_code = 'N' THEN 1 ELSE 0 END)
                    AS no_count,

                SUM(CASE WHEN vote_code = 'A' THEN 1 ELSE 0 END)
                    AS abstain_count

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
            ? AS country_code,

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
                )
                / COUNT(*),
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
                )
                / COUNT(*),
                2
            ) AS disagreement_percentage

        FROM target_votes t

        JOIN bloc_majority b
            ON t.vote_event_id = b.vote_event_id
    """

    params = [country_code] + bloc_codes + [country_code]

    return con.execute(query, params).df()