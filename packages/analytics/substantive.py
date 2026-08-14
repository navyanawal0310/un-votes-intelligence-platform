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