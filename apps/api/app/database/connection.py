"""
DuckDB database connection.
"""

from pathlib import Path

import duckdb

DATABASE_PATH = (
    Path(__file__)
    .resolve()
    .parents[4]
    / "data"
    / "warehouse"
    / "warehouse.duckdb"
)


def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Return a DuckDB connection.

    The database file is created automatically
    if it does not already exist.
    """

    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return duckdb.connect(DATABASE_PATH)