"""
Substantive disagreement analysis for UN voting comparisons.
"""

from __future__ import annotations

import duckdb
import pandas as pd


SUBSTANTIVE_VOTES = {"Y", "N", "A"}


def substantive_disagreements(
    con: duckdb.DuckDBPyConnection,
    country_a: str,
    country_b: str,
) -> pd.DataFrame:
    """
    Return voting events where two countries had substantive
    differences in their votes.

    Substantive votes:
        Y = YES
        N = NO
        A = ABSTAIN

    ABSENT votes are excluded because absence is treated as
    non-participation rather than a substantive voting position.

    Grain:
        One country-pair disagreement for one voting event.
    """

    country_a = country_a.strip().upper()
    country_b = country_b.strip().upper()

    if country_a == country_b:
        raise ValueError(
            "country_a and country_b must be different."
        )

    query = """
        SELECT
            fa.vote_event_id,

            dr.resolution_code,
            dr.resolution_title,
            dr.agenda_title,
            dr.subjects,
            dr.session,
            dr.undl_id,
            dr.undl_link,

            dd.full_date,
            dd.year,

            fa.vote_code AS country_a_vote_code,
            fa.vote_label AS country_a_vote,

            fb.vote_code AS country_b_vote_code,
            fb.vote_label AS country_b_vote

        FROM fact_votes fa

        INNER JOIN fact_votes fb
            ON fa.vote_event_id = fb.vote_event_id

        INNER JOIN dim_country ca
            ON fa.country_id = ca.country_id

        INNER JOIN dim_country cb
            ON fb.country_id = cb.country_id

        LEFT JOIN dim_resolution dr
            ON fa.resolution_id = dr.resolution_id

        LEFT JOIN dim_date dd
            ON fa.date_id = dd.date_id

        WHERE ca.ms_code = ?
          AND cb.ms_code = ?

          -- Both countries must have cast substantive votes.
          AND fa.vote_code IN ('Y', 'N', 'A')
          AND fb.vote_code IN ('Y', 'N', 'A')

          -- The substantive votes must differ.
          AND fa.vote_code != fb.vote_code

        ORDER BY
            dd.full_date,
            dr.resolution_code
    """

    result = con.execute(
        query,
        [country_a, country_b],
    ).df()

    return result

def top_disputed_resolutions(
    con: duckdb.DuckDBPyConnection,
    country_a: str,
    country_b: str,
    limit: int = 20,
) -> pd.DataFrame:
    """
    Rank resolutions by the number of substantive disagreements
    between two countries.

    ABSENT votes are excluded.

    Returns one row per resolution.
    """

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    disagreements = substantive_disagreements(
        con,
        country_a,
        country_b,
    )

    if disagreements.empty:
        return pd.DataFrame(
            columns=[
                "resolution_code",
                "resolution_title",
                "full_date",
                "year",
                "disagreement_count",
                "country_a",
                "country_b",
            ]
        )

    result = (
        disagreements
        .groupby(
            [
                "resolution_code",
                "resolution_title",
                "full_date",
                "year",
            ],
            dropna=False,
        )
        .size()
        .reset_index(name="disagreement_count")
    )

    result["country_a"] = country_a.strip().upper()
    result["country_b"] = country_b.strip().upper()

    result = (
        result
        .sort_values(
            [
                "disagreement_count",
                "full_date",
            ],
            ascending=[False, True],
        )
        .head(limit)
        .reset_index(drop=True)
    )

    return result

def substantive_disagreement_by_year(
    con: duckdb.DuckDBPyConnection,
    country_a: str,
    country_b: str,
) -> pd.DataFrame:
    """
    Calculate substantive voting agreement/disagreement by year.

    ABSENT votes are excluded.
    """

    disagreements = substantive_disagreements(
        con,
        country_a,
        country_b,
    )

    # Get all substantive comparisons, not only disagreements.
    query = """
        SELECT
            ca.ms_code AS country_a,
            cb.ms_code AS country_b,
            d.year,

            COUNT(*) AS substantive_voting_events,

            SUM(
                CASE
                    WHEN a.vote_code = b.vote_code
                    THEN 1
                    ELSE 0
                END
            ) AS matching_votes,

            SUM(
                CASE
                    WHEN a.vote_code != b.vote_code
                    THEN 1
                    ELSE 0
                END
            ) AS different_votes

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

        WHERE ca.ms_code = ?
          AND cb.ms_code = ?

          AND a.vote_code IN ('Y', 'N', 'A')
          AND b.vote_code IN ('Y', 'N', 'A')

        GROUP BY
            ca.ms_code,
            cb.ms_code,
            d.year

        ORDER BY
            d.year
    """

    result = con.execute(
        query,
        [
            country_a.strip().upper(),
            country_b.strip().upper(),
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

def substantive_disagreement_by_subject(
    con: duckdb.DuckDBPyConnection,
    country_a: str,
    country_b: str,
    min_events: int = 10,
) -> pd.DataFrame:
    """
    Calculate substantive voting disagreement by UN resolution subject.

    Only substantive votes are included:

        Y = YES
        N = NO
        A = ABSTAIN

    ABSENT and other non-substantive voting states are excluded.

    A resolution may have multiple subjects. Therefore, a single
    voting event may contribute to multiple subject categories.
    """

    query = """
        WITH vote_comparison AS (

            SELECT
                a.vote_event_id,
                a.vote_code AS country_a_vote,
                b.vote_code AS country_b_vote,
                r.resolution_id,
                r.subjects

            FROM fact_votes a

            JOIN fact_votes b
                ON a.vote_event_id = b.vote_event_id
               AND a.country_id != b.country_id

            JOIN dim_country ca
                ON a.country_id = ca.country_id

            JOIN dim_country cb
                ON b.country_id = cb.country_id

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
                resolution_id,
                TRIM(subject) AS subject

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
            ) AS t(subject)

            WHERE TRIM(subject) <> ''
        )

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
                    WHEN country_a_vote != country_b_vote
                    THEN 1
                    ELSE 0
                END
            ) AS different_votes

        FROM subject_events

        GROUP BY subject

        ORDER BY
            different_votes DESC,
            substantive_voting_events DESC
    """

    result = con.execute(
        query,
        [
            country_a.strip().upper(),
            country_b.strip().upper(),
        ],
    ).df()

    if result.empty:
        return result
    result = result[
    result["substantive_voting_events"] >= min_events
    ].copy()
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

def top_substantive_disagreement_subjects(
    con,
    country_a: str,
    country_b: str,
    limit: int = 20,
    min_events: int = 10,
) -> pd.DataFrame:
    """
    Return the subjects with the highest substantive disagreement
    between two countries.

    Subjects must have at least `min_events` comparable votes.
    """

    result = substantive_disagreement_by_subject(
        con,
        country_a,
        country_b,
        min_events=min_events,
    )

    if result.empty:
        return result

    return (
        result
        .sort_values(
            [
                "disagreement_percentage",
                "different_votes",
            ],
            ascending=[False, False],
        )
        .head(limit)
        .reset_index(drop=True)
    )