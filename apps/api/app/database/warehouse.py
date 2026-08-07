"""
Warehouse initialization.
"""

from pathlib import Path

from apps.api.app.database.connection import get_connection


SQL_DIR = (
    Path(__file__).parent
    / "sql"
)


def initialize_warehouse() -> None:
    """
    Create warehouse tables.
    """

    conn = get_connection()

    for file_name in [
        "create_dimensions.sql",
        "create_facts.sql",
    ]:

        sql = (
            SQL_DIR / file_name
        ).read_text()

        conn.execute(sql)

    conn.close()