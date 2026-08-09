"""
DuckDB warehouse loading utilities.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


class WarehouseLoader:
    """Load warehouse DataFrames into DuckDB."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

        self.connection = duckdb.connect(
            str(database_path)
        )

    def load_dataframe(
        self,
        dataframe: pd.DataFrame,
        table_name: str,
        if_exists: str = "replace",
    ) -> None:
        """Load a pandas DataFrame into a DuckDB table."""

        if if_exists == "replace":
            self.connection.execute(
                f"DROP TABLE IF EXISTS {table_name}"
            )

        self.connection.register(
            "temp_dataframe",
            dataframe,
        )

        self.connection.execute(
            f"""
            CREATE TABLE {table_name} AS
            SELECT *
            FROM temp_dataframe
            """
        )

        self.connection.unregister(
            "temp_dataframe"
        )

    def query(self, sql: str) -> pd.DataFrame:
        """Execute SQL and return the result as a DataFrame."""

        return self.connection.execute(sql).df()

    def close(self) -> None:
        """Close the DuckDB connection."""

        self.connection.close()