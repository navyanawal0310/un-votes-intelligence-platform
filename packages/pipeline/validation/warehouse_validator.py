"""
Validation checks for the UN voting warehouse.
"""

from __future__ import annotations

import duckdb


REQUIRED_TABLES = {
    "dim_body",
    "dim_country",
    "dim_date",
    "dim_resolution",
    "fact_votes",
}

VALID_VOTE_CODES = {
    "Y",
    "N",
    "A",
    "X",
}

VALID_VOTE_LABELS = {
    "YES",
    "NO",
    "ABSTAIN",
    "ABSENT",
}


def validate_warehouse(con: duckdb.DuckDBPyConnection) -> None:
    """
    Validate the loaded UN voting warehouse.

    Checks:
        1. Required tables exist.
        2. Dimension tables are non-empty.
        3. Fact table is non-empty.
        4. Dimension primary keys are unique.
        5. Fact foreign keys resolve.
        6. Vote codes and labels are valid.
        7. Fact grain is unique.
        8. Fact row count matches the canonical source expectation.
    """

    print("\n" + "=" * 60)
    print("WAREHOUSE VALIDATION")
    print("=" * 60)

    # ---------------------------------------------------------
    # 1. Required tables
    # ---------------------------------------------------------

    tables = {
        row[0]
        for row in con.execute(
            "SHOW TABLES"
        ).fetchall()
    }

    missing_tables = REQUIRED_TABLES - tables

    if missing_tables:
        raise AssertionError(
            f"Missing warehouse tables: {sorted(missing_tables)}"
        )

    print("Required tables: PASSED")

    # ---------------------------------------------------------
    # 2. Dimension and fact row counts
    # ---------------------------------------------------------

    expected_non_empty = [
        "dim_body",
        "dim_country",
        "dim_date",
        "dim_resolution",
        "fact_votes",
    ]

    row_counts = {}

    for table in expected_non_empty:
        count = con.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

        row_counts[table] = count

        if count == 0:
            raise AssertionError(
                f"{table} is empty."
            )

    print("Table row-count validation: PASSED")

    # ---------------------------------------------------------
    # 3. Dimension primary-key uniqueness
    # ---------------------------------------------------------

    dimension_keys = {
        "dim_body": "body_id",
        "dim_country": "country_id",
        "dim_date": "date_id",
        "dim_resolution": "resolution_id",
    }

    for table, key in dimension_keys.items():

        duplicate_count = con.execute(
            f"""
            SELECT COUNT(*)
            FROM (
                SELECT {key}
                FROM {table}
                GROUP BY {key}
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]

        if duplicate_count > 0:
            raise AssertionError(
                f"{table}.{key} contains duplicate keys: "
                f"{duplicate_count}"
            )

    print("Dimension-key validation: PASSED")

    # ---------------------------------------------------------
    # 4. Fact foreign-key validation
    # ---------------------------------------------------------

    foreign_key_checks = {
        "body_id": "dim_body",
        "country_id": "dim_country",
        "date_id": "dim_date",
        "resolution_id": "dim_resolution",
    }

    for column, dimension in foreign_key_checks.items():

        unresolved = con.execute(
            f"""
            SELECT COUNT(*)
            FROM fact_votes f
            LEFT JOIN {dimension} d
                ON f.{column} = d.{column}
            WHERE d.{column} IS NULL
            """
        ).fetchone()[0]

        if unresolved > 0:
            raise AssertionError(
                f"Unresolved foreign keys in fact_votes.{column}: "
                f"{unresolved}"
            )

    print("Foreign-key validation: PASSED")

    # ---------------------------------------------------------
    # 5. Vote-code validation
    # ---------------------------------------------------------

    invalid_codes = con.execute(
        """
        SELECT DISTINCT vote_code
        FROM fact_votes
        WHERE vote_code NOT IN ('Y', 'N', 'A', 'X')
        """
    ).fetchall()

    if invalid_codes:
        raise AssertionError(
            "Invalid vote codes found: "
            f"{[row[0] for row in invalid_codes]}"
        )

    print("Vote-code validation: PASSED")

    # ---------------------------------------------------------
    # 6. Vote-label validation
    # ---------------------------------------------------------

    invalid_labels = con.execute(
        """
        SELECT DISTINCT vote_label
        FROM fact_votes
        WHERE vote_label NOT IN (
            'YES',
            'NO',
            'ABSTAIN',
            'ABSENT'
        )
        """
    ).fetchall()

    if invalid_labels:
        raise AssertionError(
            "Invalid vote labels found: "
            f"{[row[0] for row in invalid_labels]}"
        )

    print("Vote-label validation: PASSED")

    # ---------------------------------------------------------
    # 7. Vote-code / vote-label consistency
    # ---------------------------------------------------------

    inconsistent_votes = con.execute(
        """
        SELECT COUNT(*)
        FROM fact_votes
        WHERE
            (vote_code = 'Y' AND vote_label != 'YES')
            OR
            (vote_code = 'N' AND vote_label != 'NO')
            OR
            (vote_code = 'A' AND vote_label != 'ABSTAIN')
            OR
            (vote_code = 'X' AND vote_label != 'ABSENT')
        """
    ).fetchone()[0]

    if inconsistent_votes > 0:
        raise AssertionError(
            "Vote code / label inconsistencies found: "
            f"{inconsistent_votes}"
        )

    print("Vote consistency validation: PASSED")

    # ---------------------------------------------------------
    # 8. Vote-score validation
    # ---------------------------------------------------------

    invalid_scores = con.execute(
        """
        SELECT COUNT(*)
        FROM fact_votes
        WHERE
            (vote_code = 'Y' AND vote_score != 1.0)
            OR
            (vote_code = 'N' AND vote_score != -1.0)
            OR
            (vote_code = 'A' AND vote_score != 0.0)
            OR
            (vote_code = 'X' AND vote_score IS NOT NULL)
        """
    ).fetchone()[0]

    if invalid_scores > 0:
        raise AssertionError(
            "Invalid vote scores found: "
            f"{invalid_scores}"
        )

    print("Vote-score validation: PASSED")

    # ---------------------------------------------------------
    # 9. Fact-table grain validation
    # ---------------------------------------------------------

    duplicate_votes = con.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT
                vote_event_id,
                country_id
            FROM fact_votes
            GROUP BY
                vote_event_id,
                country_id
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    if duplicate_votes > 0:
        raise AssertionError(
            "Fact-table grain violation detected: "
            f"{duplicate_votes} duplicate "
            "(vote_event_id, country_id) combinations."
        )

    print("Fact-grain validation: PASSED")

    # ---------------------------------------------------------
    # 10. Required fact columns must not be NULL
    # ---------------------------------------------------------

    required_fact_columns = [
        "vote_event_id",
        "body_id",
        "resolution_id",
        "country_id",
        "date_id",
        "vote_code",
        "vote_label",
    ]

    for column in required_fact_columns:

        null_count = con.execute(
            f"""
            SELECT COUNT(*)
            FROM fact_votes
            WHERE {column} IS NULL
            """
        ).fetchone()[0]

        if null_count > 0:
            raise AssertionError(
                f"NULL values found in fact_votes.{column}: "
                f"{null_count}"
            )

    print("Fact-null validation: PASSED")

    # ---------------------------------------------------------
    # 11. Warehouse summary
    # ---------------------------------------------------------

    print("\nWAREHOUSE COUNTS")
    print("-" * 60)

    for table, count in row_counts.items():
        print(f"{table:20} {count:>12,}")

    print("\n" + "=" * 60)
    print("WAREHOUSE VALIDATION: PASSED")
    print("=" * 60)