"""
DuckDB schema definitions for the UN voting warehouse.
"""

from __future__ import annotations

import duckdb


def create_schema(con: duckdb.DuckDBPyConnection) -> None:
    """
    Create the UN voting warehouse tables.
    """

    # ---------------------------------------------------------
    # Body dimension
    # ---------------------------------------------------------

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS dim_body (
            body_id INTEGER PRIMARY KEY,
            body_code VARCHAR NOT NULL,
            body_name VARCHAR NOT NULL
        )
        """
    )

    # ---------------------------------------------------------
    # Country dimension
    # ---------------------------------------------------------

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS dim_country (
            country_id INTEGER PRIMARY KEY,
            ms_code VARCHAR NOT NULL,
            country_name VARCHAR NOT NULL
        )
        """
    )

    # ---------------------------------------------------------
    # Date dimension
    # ---------------------------------------------------------

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS dim_date (
            date_id INTEGER PRIMARY KEY,
            full_date DATE,
            year INTEGER NOT NULL,
            quarter INTEGER,
            month INTEGER,
            month_name VARCHAR,
            day INTEGER,
            day_name VARCHAR,
            date_precision VARCHAR NOT NULL
        )
        """
    )

    # ---------------------------------------------------------
    # Resolution dimension
    # ---------------------------------------------------------

    con.execute(
    """
        CREATE TABLE IF NOT EXISTS dim_resolution (
            resolution_id INTEGER PRIMARY KEY,
            resolution_code VARCHAR NOT NULL,
            resolution_title VARCHAR,
            agenda_title VARCHAR,
            subjects VARCHAR,
            session VARCHAR,
            undl_id BIGINT,
            undl_link VARCHAR
        )
        """
    )

    # ---------------------------------------------------------
    # Fact table
    # ---------------------------------------------------------

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS fact_votes (
            vote_event_id BIGINT NOT NULL,
            body_id INTEGER NOT NULL,
            resolution_id INTEGER NOT NULL,
            country_id INTEGER NOT NULL,
            date_id INTEGER NOT NULL,
            vote_code VARCHAR NOT NULL,
            vote_label VARCHAR NOT NULL,
            vote_score DOUBLE
        )
        """
    )