"""
Generic DuckDB warehouse loader.
"""

from __future__ import annotations

import duckdb
import pandas as pd

from apps.api.app.database.connection import get_connection


class WarehouseLoader:
    """
    Generic loader for DuckDB warehouse tables.
    """

    def __init__(self) -> None:
        self.connection = get_connection()

    def load_dataframe(
        self,
        dataframe: pd.DataFrame,
        table_name: str,
        if_exists: str = "append",
    ) -> None:
        """
        Load a pandas DataFrame into a DuckDB table.

        Parameters
        ----------
        dataframe : pd.DataFrame
            Data to load.

        table_name : str
            Target table.

        if_exists : str
            append | replace
        """

        if if_exists not in {"append", "replace"}:
            raise ValueError(
                "if_exists must be 'append' or 'replace'"
            )

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
            CREATE TABLE IF NOT EXISTS {table_name}
            AS
            SELECT *
            FROM temp_dataframe
            """
        )

        if if_exists == "append":
            self.connection.execute(
                f"""
                INSERT INTO {table_name}
                SELECT *
                FROM temp_dataframe
                """
            )

        self.connection.unregister(
            "temp_dataframe"
        )

    def query(self, sql: str):
        """
        Execute SQL and return a DataFrame.
        """

        return self.connection.sql(sql).df()

    def close(self) -> None:
        """
        Close warehouse connection.
        """

        self.connection.close()