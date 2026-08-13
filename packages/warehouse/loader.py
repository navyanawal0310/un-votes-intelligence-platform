"""
Warehouse loading pipeline for official UN voting data.
"""

from __future__ import annotations

import pandas as pd

from packages.common.paths import RAW_DATA_DIR
from packages.common.constants import DATASET_FILENAME
from packages.pipeline.ingestion.ga_loader import load_ga_dataset
from packages.pipeline.transformation.canonical import normalize_votes

from packages.warehouse.database import get_connection
from packages.warehouse.schema import create_schema
from packages.warehouse.dimensions import (
    build_dim_body,
    build_dim_country,
    build_dim_date,
    build_dim_resolution,
)
from packages.warehouse.facts import build_fact_votes


def load_ga_warehouse() -> None:
    """
    Build and load the General Assembly warehouse.

    Pipeline:
        raw GA dataset
        -> canonical dataset
        -> dimensions
        -> fact_votes
        -> DuckDB
    """

    print("Loading official General Assembly dataset...")

    source_path = RAW_DATA_DIR / DATASET_FILENAME

    df = load_ga_dataset(source_path)

    print(f"Source rows: {len(df):,}")

    # ---------------------------------------------------------
    # Canonical transformation
    # ---------------------------------------------------------

    print("\nApplying canonical transformation...")

    canonical_df = normalize_votes(
        df,
        body_code="GA",
    )

    print(f"Canonical rows: {len(canonical_df):,}")

    # ---------------------------------------------------------
    # Build dimensions
    # ---------------------------------------------------------

    print("\nBuilding dimensions...")

    dim_body = build_dim_body(canonical_df)
    dim_country = build_dim_country(canonical_df)
    dim_date = build_dim_date(canonical_df)
    dim_resolution = build_dim_resolution(canonical_df)

    print(f"dim_body:       {len(dim_body):,} rows")
    print(f"dim_country:    {len(dim_country):,} rows")
    print(f"dim_date:       {len(dim_date):,} rows")
    print(f"dim_resolution: {len(dim_resolution):,} rows")

    # ---------------------------------------------------------
    # Build fact table
    # ---------------------------------------------------------

    print("\nBuilding fact_votes...")

    fact_votes = build_fact_votes(
        canonical_df=canonical_df,
        dim_body=dim_body,
        dim_date=dim_date,
        dim_country=dim_country,
        dim_resolution=dim_resolution,
    )

    print(f"fact_votes:     {len(fact_votes):,} rows")

    # ---------------------------------------------------------
    # Load DuckDB
    # ---------------------------------------------------------

    print("\nLoading warehouse...")

    con = get_connection()

    try:
        create_schema(con)

        # Replace existing warehouse contents.
        con.execute("DELETE FROM fact_votes")
        con.execute("DELETE FROM dim_resolution")
        con.execute("DELETE FROM dim_date")
        con.execute("DELETE FROM dim_country")
        con.execute("DELETE FROM dim_body")

        # -----------------------------------------------------
        # Dimensions
        # -----------------------------------------------------

        con.register("dim_body_df", dim_body)
        con.register("dim_country_df", dim_country)
        con.register("dim_date_df", dim_date)
        con.register("dim_resolution_df", dim_resolution)

        con.execute(
            """
            INSERT INTO dim_body
            SELECT * FROM dim_body_df
            """
        )

        con.execute(
            """
            INSERT INTO dim_country
            SELECT * FROM dim_country_df
            """
        )

        con.execute(
            """
            INSERT INTO dim_date
            SELECT * FROM dim_date_df
            """
        )

        con.execute(
            """
            INSERT INTO dim_resolution
            SELECT * FROM dim_resolution_df
            """
        )

        # -----------------------------------------------------
        # Fact
        # -----------------------------------------------------

        con.register("fact_votes_df", fact_votes)

        con.execute(
            """
            INSERT INTO fact_votes
            SELECT * FROM fact_votes_df
            """
        )

        # -----------------------------------------------------
        # Warehouse validation
        # -----------------------------------------------------

        print("\nWAREHOUSE COUNTS")
        print("-" * 50)

        tables = [
            "dim_body",
            "dim_country",
            "dim_date",
            "dim_resolution",
            "fact_votes",
        ]

        for table in tables:
            count = con.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            print(f"{table:20} {count:,}")

    finally:
        con.close()

    print("\nWAREHOUSE LOAD: PASSED")