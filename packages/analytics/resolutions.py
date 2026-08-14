"""
Resolution-level analysis for UN voting comparisons.
"""

from __future__ import annotations

import duckdb
import pandas as pd


def country_disagreements(
    con: duckdb.DuckDBPyConnection,
    country_a: str,
    country_b: str,
) -> pd.DataFrame:
    """
    Return UN voting events where two countries voted differently.

    Grain:
        One disagreement for one voting event.

    Parameters
    ----------
    con:
        Active DuckDB connection.

    country_a:
        First Member State code.

    country_b:
        Second Member State code.

    Returns
    -------
    pd.DataFrame
        Resolution-level disagreements between the two countries.
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