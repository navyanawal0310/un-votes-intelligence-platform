"""
Analytical queries for the UN Votes warehouse.
"""

from __future__ import annotations

from .connection import get_connection


def country_vote_distribution(country_name: str):
    """
    Return vote counts for a country.
    """

    query = """
        SELECT
            f.vote_code,
            f.vote_label,
            COUNT(*) AS vote_count
        FROM fact_votes AS f
        JOIN dim_country AS c
            ON f.country_id = c.country_id
        WHERE c.country_name = ?
        GROUP BY
            f.vote_code,
            f.vote_label
        ORDER BY f.vote_code
    """

    connection = get_connection()

    try:
        return connection.execute(
            query,
            [country_name],
        ).fetchdf()
    finally:
        connection.close()


def country_vote_history(country_name: str):
    """
    Return chronological voting history for a country.
    """

    query = """
        SELECT
            d.full_date,
            d.year,
            r.resolution_code,
            r.resolution_title,
            council.council_name,
            f.vote_code,
            f.vote_label,
            f.vote_score
        FROM fact_votes AS f

        JOIN dim_country AS c
            ON f.country_id = c.country_id

        JOIN dim_date AS d
            ON f.date_id = d.date_id

        JOIN dim_resolution AS r
            ON f.resolution_id = r.resolution_id

        JOIN dim_council AS council
            ON f.council_id = council.council_id

        WHERE c.country_name = ?

        ORDER BY
            d.full_date,
            r.resolution_code
    """

    connection = get_connection()

    try:
        return connection.execute(
            query,
            [country_name],
        ).fetchdf()
    finally:
        connection.close()


def council_vote_distribution(council_name: str):
    """
    Return vote distribution for a UN council.
    """

    query = """
        SELECT
            f.vote_code,
            f.vote_label,
            COUNT(*) AS vote_count
        FROM fact_votes AS f

        JOIN dim_council AS c
            ON f.council_id = c.council_id

        WHERE c.council_name = ?

        GROUP BY
            f.vote_code,
            f.vote_label

        ORDER BY f.vote_code
    """

    connection = get_connection()

    try:
        return connection.execute(
            query,
            [council_name],
        ).fetchdf()
    finally:
        connection.close()


def most_contested_resolutions(limit: int = 20):
    """
    Return resolutions with the strongest YES/NO opposition.
    """

    query = """
        SELECT
            r.resolution_id,
            r.resolution_code,
            r.resolution_title,
            c.council_name,

            COUNT(*) AS total_votes,

            SUM(
                CASE
                    WHEN f.vote_code = 'Y' THEN 1
                    ELSE 0
                END
            ) AS yes_votes,

            SUM(
                CASE
                    WHEN f.vote_code = 'N' THEN 1
                    ELSE 0
                END
            ) AS no_votes,

            SUM(
                CASE
                    WHEN f.vote_code = 'A' THEN 1
                    ELSE 0
                END
            ) AS abstain_votes

        FROM fact_votes AS f

        JOIN dim_resolution AS r
            ON f.resolution_id = r.resolution_id

        JOIN dim_council AS c
            ON f.council_id = c.council_id

        GROUP BY
            r.resolution_id,
            r.resolution_code,
            r.resolution_title,
            c.council_name

        HAVING
            yes_votes > 0
            AND no_votes > 0

        ORDER BY
            LEAST(yes_votes, no_votes) DESC,
            total_votes DESC

        LIMIT ?
    """

    connection = get_connection()

    try:
        return connection.execute(
            query,
            [limit],
        ).fetchdf()
    finally:
        connection.close()