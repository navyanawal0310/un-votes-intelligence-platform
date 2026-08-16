"""
Temporal change-point detection for UN issue positions.

Detects statistically significant shifts in a country's
voting position on an issue.

The input is the output of issue_positions().
"""

from __future__ import annotations

import duckdb
import pandas as pd
import numpy as np


def detect_change_points(
    con: duckdb.DuckDBPyConnection,
    country_code: str,
    issue: str,
    min_events: int = 3,
    min_shift: float = 0.20,
) -> pd.DataFrame:
    """
    Detect year-to-year changes in an issue position.

    Position score ranges from -1 to +1.

    A change is flagged when the absolute difference between
    consecutive yearly positions is >= min_shift.

    Parameters
    ----------
    con:
        Active DuckDB connection.

    country_code:
        UN Member State code, e.g. IND.

    issue:
        Exact subject string from dim_resolution.subjects.

    min_events:
        Minimum voting events required for each yearly observation.

    min_shift:
        Minimum absolute position change required.

    Returns
    -------
    pandas.DataFrame
    """

    if not country_code.strip():
        raise ValueError("country_code cannot be empty.")

    if not issue.strip():
        raise ValueError("issue cannot be empty.")

    if min_events < 1:
        raise ValueError("min_events must be >= 1.")

    if min_shift <= 0 or min_shift > 2:
        raise ValueError(
            "min_shift must be > 0 and <= 2."
        )

    query = """
        WITH yearly AS (

            SELECT
                c.ms_code AS country_code,
                r.subjects AS issue,
                d.year,

                COUNT(*) AS voting_events,

                ROUND(
                    SUM(
                        CASE
                            WHEN f.vote_code = 'Y' THEN 1
                            WHEN f.vote_code = 'N' THEN -1
                            ELSE 0
                        END
                    ) * 1.0 / COUNT(*),
                    4
                ) AS position_score

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

            GROUP BY
                c.ms_code,
                r.subjects,
                d.year

            HAVING COUNT(*) >= ?

            ORDER BY d.year
        )

        SELECT
            country_code,
            issue,
            year,
            voting_events,
            position_score

        FROM yearly
        ORDER BY year
    """

    df = con.execute(
        query,
        [
            country_code.strip().upper(),
            issue.strip(),
            min_events,
        ],
    ).df()

    if df.empty:
        return pd.DataFrame(
            columns=[
                "country_code",
                "issue",
                "change_year",
                "previous_year",
                "previous_score",
                "new_score",
                "position_shift",
                "absolute_shift",
                "significant_change",
            ]
        )

    df["previous_year"] = df["year"].shift(1)
    df["previous_score"] = df["position_score"].shift(1)

    df["position_shift"] = (
        df["position_score"] -
        df["previous_score"]
    )

    df["absolute_shift"] = (
        df["position_shift"].abs()
    )

    df["significant_change"] = (
        df["absolute_shift"] >= min_shift
    )

    changes = df[
        df["significant_change"]
    ].copy()

    changes = changes.rename(
        columns={
            "year": "change_year",
            "position_score": "new_score",
        }
    )

    return changes[
        [
            "country_code",
            "issue",
            "change_year",
            "previous_year",
            "previous_score",
            "new_score",
            "position_shift",
            "absolute_shift",
            "significant_change",
        ]
    ].reset_index(drop=True)


def rank_change_points(
    con: duckdb.DuckDBPyConnection,
    country_code: str,
    min_events: int = 3,
    min_shift: float = 0.20,
) -> pd.DataFrame:
    """
    Find the largest issue-level position changes for a country.

    This scans all issues available for the country.
    """

    country_code = country_code.strip().upper()

    query = """
        WITH yearly AS (

            SELECT
                c.ms_code AS country_code,
                r.subjects AS issue,
                d.year,

                COUNT(*) AS voting_events,

                SUM(
                    CASE
                        WHEN f.vote_code = 'Y' THEN 1
                        WHEN f.vote_code = 'N' THEN -1
                        ELSE 0
                    END
                ) * 1.0 / COUNT(*) AS position_score

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

            GROUP BY
                c.ms_code,
                r.subjects,
                d.year

            HAVING COUNT(*) >= ?
        ),

        with_previous AS (

            SELECT
                *,
                LAG(year) OVER (
                    PARTITION BY issue
                    ORDER BY year
                ) AS previous_year,

                LAG(position_score) OVER (
                    PARTITION BY issue
                    ORDER BY year
                ) AS previous_score

            FROM yearly
        )

        SELECT
            country_code,
            issue,
            previous_year,
            year AS change_year,
            previous_score,
            position_score AS new_score,

            position_score - previous_score
                AS position_shift,

            ABS(
                position_score - previous_score
            ) AS absolute_shift

        FROM with_previous

        WHERE previous_score IS NOT NULL
          AND ABS(
              position_score - previous_score
          ) >= ?

        ORDER BY absolute_shift DESC
    """

    return con.execute(
        query,
        [
            country_code,
            min_events,
            min_shift,
        ],
    ).df()