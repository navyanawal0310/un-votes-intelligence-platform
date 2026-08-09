"""
Build and load the complete UN Votes warehouse into DuckDB.
"""

from pathlib import Path

from packages.common.constants import DATASET_FILENAME
from packages.common.paths import DOWNLOADS_DIR

from packages.pipeline.profiling.analyzer import load_dataset
from packages.pipeline.transformation.unpivot import unpivot_dataset

from packages.warehouse.dimensions import (
    build_dim_council,
    build_dim_country,
    build_dim_date,
    build_dim_resolution,
)

from packages.warehouse.facts import build_fact_votes

from apps.api.app.database.warehouse import WarehouseLoader


DATABASE_PATH = Path(
    "data/warehouse/warehouse.duckdb"
)


def main() -> None:

    print("Loading source dataset...")

    df = load_dataset(
        DOWNLOADS_DIR / DATASET_FILENAME
    )

    print("Transforming dataset...")

    long_df = unpivot_dataset(df)

    print("Building dimensions...")

    dim_council = build_dim_council(long_df)
    dim_country = build_dim_country(long_df)
    dim_date = build_dim_date(long_df)
    dim_resolution = build_dim_resolution(long_df)

    print("Building fact table...")

    fact_votes = build_fact_votes(
        long_df,
        dim_council,
        dim_date,
        dim_country,
        dim_resolution,
    )

    print("Connecting to DuckDB...")

    loader = WarehouseLoader(
        DATABASE_PATH
    )

    print("Loading dimension tables...")

    loader.load_dataframe(
        dim_council,
        "dim_council",
    )

    loader.load_dataframe(
        dim_country,
        "dim_country",
    )

    loader.load_dataframe(
        dim_date,
        "dim_date",
    )

    loader.load_dataframe(
        dim_resolution,
        "dim_resolution",
    )

    print("Loading fact table...")

    loader.load_dataframe(
        fact_votes,
        "fact_votes",
    )

    print("\nWAREHOUSE LOAD COMPLETE")
    print("-" * 60)

    tables = loader.query(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
        ORDER BY table_name
        """
    )

    print(tables.to_string(index=False))

    print("\nROW COUNTS")
    print("-" * 60)

    for table in [
        "dim_council",
        "dim_country",
        "dim_date",
        "dim_resolution",
        "fact_votes",
    ]:
        result = loader.query(
            f"SELECT COUNT(*) AS row_count FROM {table}"
        )

        print(
            f"{table:<20} {result.iloc[0]['row_count']:,}"
        )

    loader.close()


if __name__ == "__main__":
    main()