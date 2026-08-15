"""
Subject-level voting similarity rankings.

Ranks UN subjects by agreement or disagreement between two countries.
"""

from __future__ import annotations

import duckdb
import pandas as pd


def subject_rankings(
    con: duckdb.DuckDBPyConnection,
    country_a: str,
    country_b: str,
    min_events: int = 5,
    order_by: str = "disagreement",
) -> pd.DataFrame:
    """
    Rank subjects by voting agreement or disagreement.

    Only substantive votes are considered:

        Y = YES
        N = NO
        A = ABSTAIN

    Absence and non-voting are excluded.

    Parameters
    ----------
    con:
        DuckDB connection.

    country_a:
        First country UN Member State code.

    country_b:
        Second country UN Member State code.

    min_events:
        Minimum number of substantive voting events required.

    order_by:
        "disagreement" or "agreement".
    """

    if country_a == country_b:
        raise ValueError(
            "country_a and country_b must be different."
        )

    if min_events < 1:
        raise ValueError(
            "min_events must be at least 1."
        )

    if order_by not in {"agreement", "disagreement"}:
        raise ValueError(
            "order_by must be 'agreement' or 'disagreement'."
        )

    query = """
        WITH country_votes AS (
            SELECT
                f.vote_event_id,
                f.country_id,
                f.vote_code,
                r.subjects AS subject
            FROM fact_votes f
            JOIN dim_resolution r
                ON f.resolution_id = r.resolution_id
            JOIN dim_country c
                ON f.country_id = c.country_id
            WHERE c.ms_code IN (?, ?)
              AND f.vote_code IN ('Y', 'N', 'A')
              AND r.subjects IS NOT NULL
        ),

        paired_votes AS (
            SELECT
                a.vote_event_id,
                a.subject,
                a.vote_code AS country_a_vote,
                b.vote_code AS country_b_vote
            FROM country_votes a
            JOIN country_votes b
                ON a.vote_event_id = b.vote_event_id
               AND a.subject = b.subject
               AND a.country_id <> b.country_id
            JOIN dim_country ca
                ON a.country_id = ca.country_id
            JOIN dim_country cb
                ON b.country_id = cb.country_id
            WHERE ca.ms_code = ?
              AND cb.ms_code = ?
        ),

        subject_summary AS (
            SELECT
                subject,

                COUNT(*) AS substantive_voting_events,

                SUM(
                    CASE
                        WHEN country_a_vote = country_b_vote
                        THEN 1
                        ELSE 0
                    END
                ) AS matching_votes,

                SUM(
                    CASE
                        WHEN country_a_vote <> country_b_vote
                        THEN 1
                        ELSE 0
                    END
                ) AS different_votes

            FROM paired_votes

            GROUP BY subject

            HAVING COUNT(*) >= ?
        )

        SELECT
            subject,
            substantive_voting_events,
            matching_votes,
            different_votes,

            ROUND(
                100.0 * matching_votes
                / substantive_voting_events,
                2
            ) AS agreement_percentage,

            ROUND(
                100.0 * different_votes
                / substantive_voting_events,
                2
            ) AS disagreement_percentage

        FROM subject_summary

        ORDER BY
    """

    if order_by == "disagreement":
        query += """
            disagreement_percentage DESC,
            substantive_voting_events DESC,
            subject
        """
    else:
        query += """
            agreement_percentage DESC,
            substantive_voting_events DESC,
            subject
        """

    return con.execute(
        query,
        [
            country_a,
            country_b,
            country_a,
            country_b,
            min_events,
        ],
    ).df()