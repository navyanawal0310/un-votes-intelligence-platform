"""
Classification and aggregation of UN voting disagreements.
"""

from __future__ import annotations

import duckdb
import pandas as pd


def disagreement_summary(
    con: duckdb.DuckDBPyConnection,
    country_a: str,
    country_b: str,
) -> pd.DataFrame:
    """
    Summarize how two countries disagree in their UN votes.
    """

    country_a = country_a.strip().upper()
    country_b = country_b.strip().upper()

    if country_a == country_b:
        raise ValueError(
            "country_a and country_b must be different."
        )

    query = """
        SELECT
            fa.vote_code AS country_a_vote_code,
            fa.vote_label AS country_a_vote,

            fb.vote_code AS country_b_vote_code,
            fb.vote_label AS country_b_vote,

            COUNT(*) AS disagreement_count

        FROM fact_votes fa

        INNER JOIN fact_votes fb
            ON fa.vote_event_id = fb.vote_event_id

        INNER JOIN dim_country ca
            ON fa.country_id = ca.country_id

        INNER JOIN dim_country cb
            ON fb.country_id = cb.country_id

        WHERE ca.ms_code = ?
          AND cb.ms_code = ?

          AND fa.vote_code != fb.vote_code

        GROUP BY
            fa.vote_code,
            fa.vote_label,
            fb.vote_code,
            fb.vote_label

        ORDER BY
            disagreement_count DESC
    """

    return con.execute(
        query,
        [country_a, country_b],
    ).df()