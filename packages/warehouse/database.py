"""
DuckDB database connection utilities for the UN voting warehouse.
"""

from __future__ import annotations

import duckdb

from packages.common.paths import WAREHOUSE_DATA_DIR


DATABASE_PATH = WAREHOUSE_DATA_DIR / "un_votes.duckdb"


def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Open a connection to the UN voting DuckDB warehouse.
    """

    WAREHOUSE_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    return duckdb.connect(
        str(DATABASE_PATH)
    )