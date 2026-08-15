"""
Subject-level voting trend analysis.

Provides year-by-year substantive voting agreement and
disagreement for a selected UN subject and country pair.
"""

from __future__ import annotations

import duckdb
import pandas as pd


def subject_voting_trend(
    con: duckdb.DuckDBPyConnection,
    country_a: str,
    country_b: str,
    subject: str,
    min_events: int = 1,
) -> pd.DataFrame:
    """
    Calculate substantive voting trends for a subject.

    Grain:
        One country pair / subject / year.

    Only substantive votes are included:

        Y = YES
        N = NO
        A = ABSTAIN

    ABSENT and other non-substantive votes are excluded.

    Parameters
    ----------
    con:
        DuckDB connection.

    country_a:
        ISO-style Member State code, e.g. IND.

    country_b:
        ISO-style Member State code, e.g. CHN.

    subject:
        Exact subject string from dim_resolution.subjects.

    min_events:
        Minimum number of comparable substantive votes required
        for a year to appear in the result.

    Returns
    -------
    pd.DataFrame
        Year-by-year substantive voting trend.
    """

    query = """
        WITH vote_comparison AS (

            SELECT
                a.vote_event_id,
                a.vote_code AS country_a_vote,
                b.vote_code AS country_b_vote,
                d.year,
                r.subjects

            FROM fact_votes a

            JOIN fact_votes b
                ON a.vote_event_id = b.vote_event_id
               AND a.country_id != b.country_id

            JOIN dim_country ca
                ON a.country_id = ca.country_id

            JOIN dim_country cb
                ON b.country_id = cb.country_id

            JOIN dim_date d
                ON a.date_id = d.date_id

            JOIN dim_resolution r
                ON a.resolution_id = r.resolution_id

            WHERE ca.ms_code = ?
              AND cb.ms_code = ?

              AND a.vote_code IN ('Y', 'N', 'A')
              AND b.vote_code IN ('Y', 'N', 'A')
        ),

        subject_events AS (

            SELECT DISTINCT
                vote_event_id,
                country_a_vote,
                country_b_vote,
                year,
                TRIM(subject_value) AS subject

            FROM vote_comparison

            CROSS JOIN UNNEST(
                string_split(
                    regexp_replace(
                        COALESCE(subjects, ''),
                        '[;|]',
                        ',',
                        'g'
                    ),
                    ','
                )
            ) AS t(subject_value)

            WHERE TRIM(subject_value) <> ''
        )

        SELECT
            year,

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
                    WHEN country_a_vote != country_b_vote
                    THEN 1
                    ELSE 0
                END
            ) AS different_votes

        FROM subject_events

        WHERE LOWER(subject) = LOWER(?)

        GROUP BY year

        HAVING COUNT(*) >= ?

        ORDER BY year
    """

    result = con.execute(
        query,
        [
            country_a.strip().upper(),
            country_b.strip().upper(),
            subject.strip(),
            min_events,
        ],
    ).df()

    if result.empty:
        return pd.DataFrame(
            columns=[
                "country_a",
                "country_b",
                "subject",
                "year",
                "substantive_voting_events",
                "matching_votes",
                "different_votes",
                "agreement_percentage",
                "disagreement_percentage",
            ]
        )

    result["agreement_percentage"] = (
        result["matching_votes"]
        / result["substantive_voting_events"]
        * 100
    ).round(2)

    result["disagreement_percentage"] = (
        result["different_votes"]
        / result["substantive_voting_events"]
        * 100
    ).round(2)

    result.insert(
        0,
        "country_a",
        country_a.strip().upper(),
    )

    result.insert(
        1,
        "country_b",
        country_b.strip().upper(),
    )

    result.insert(
        2,
        "subject",
        subject.strip(),
    )

    return result

def subject_trends(
    con: duckdb.DuckDBPyConnection,
    country_a: str,
    country_b: str,
    min_events: int = 10,
) -> pd.DataFrame:
    """
    Calculate substantive voting trends across all subjects and years.

    Only subject/year combinations with at least `min_events`
    substantive voting events are returned.
    """

    query = """
        WITH vote_comparison AS (

            SELECT
                a.vote_event_id,
                a.vote_code AS country_a_vote,
                b.vote_code AS country_b_vote,
                d.year,
                r.subjects

            FROM fact_votes a

            JOIN fact_votes b
                ON a.vote_event_id = b.vote_event_id
               AND a.country_id != b.country_id

            JOIN dim_country ca
                ON a.country_id = ca.country_id

            JOIN dim_country cb
                ON b.country_id = cb.country_id

            JOIN dim_date d
                ON a.date_id = d.date_id

            JOIN dim_resolution r
                ON a.resolution_id = r.resolution_id

            WHERE ca.ms_code = ?
              AND cb.ms_code = ?

              AND a.vote_code IN ('Y', 'N', 'A')
              AND b.vote_code IN ('Y', 'N', 'A')
        ),

        subject_events AS (

            SELECT DISTINCT
                vote_event_id,
                country_a_vote,
                country_b_vote,
                year,
                TRIM(subject_value) AS subject

            FROM vote_comparison

            CROSS JOIN UNNEST(
                string_split(
                    regexp_replace(
                        COALESCE(subjects, ''),
                        '[;|]',
                        ',',
                        'g'
                    ),
                    ','
                )
            ) AS t(subject_value)

            WHERE TRIM(subject_value) <> ''
        )

        SELECT
            year,
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
                    WHEN country_a_vote != country_b_vote
                    THEN 1
                    ELSE 0
                END
            ) AS different_votes

        FROM subject_events

        GROUP BY
            year,
            subject

        HAVING COUNT(*) >= ?

        ORDER BY
            year,
            different_votes DESC
    """

    result = con.execute(
        query,
        [
            country_a.strip().upper(),
            country_b.strip().upper(),
            min_events,
        ],
    ).df()

    if result.empty:
        return result

    result["agreement_percentage"] = (
        result["matching_votes"]
        / result["substantive_voting_events"]
        * 100
    ).round(2)

    result["disagreement_percentage"] = (
        result["different_votes"]
        / result["substantive_voting_events"]
        * 100
    ).round(2)

    return result

def find_subjects(
    con,
    keyword: str,
) -> pd.DataFrame:
    """
    Find UN resolution subjects matching a keyword.

    Matching is case-insensitive and uses partial matching.
    """

    if not keyword or not keyword.strip():
        raise ValueError("Subject keyword cannot be empty.")

    query = """
        SELECT DISTINCT
            subjects AS subject
        FROM dim_resolution
        WHERE subjects IS NOT NULL
          AND LOWER(subjects) LIKE ?
        ORDER BY subjects
    """

    pattern = f"%{keyword.strip().lower()}%"

    return con.execute(
        query,
        [pattern],
    ).df()