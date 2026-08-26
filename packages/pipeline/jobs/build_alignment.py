from __future__ import annotations

from pathlib import Path

import duckdb


BASE_DIR = Path(__file__).resolve().parents[3]

GOLD_PATH = (
    BASE_DIR
    / "data"
    / "gold"
    / "country_pairs"
    / "country_pair_input.parquet"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "gold"
    / "analytical"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "country_pair_alignment.parquet"
)


def main() -> None:

    print("=" * 70)
    print("UN VOTES ANALYZER — ALL-COUNTRY ALIGNMENT")
    print("=" * 70)

    if not GOLD_PATH.exists():
        raise FileNotFoundError(
            f"Gold dataset not found: {GOLD_PATH}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    con = duckdb.connect()

    try:

        print()
        print("Reading Gold Parquet with DuckDB...")

        query = f"""
        COPY (

            WITH votes AS (

                SELECT
                    undl_id,
                    year,
                    body_code,
                    resolution,
                    ms_code,
                    vote_score

                FROM read_parquet(
                    '{GOLD_PATH.as_posix()}'
                )

                WHERE vote_score IN (-1.0, 0.0, 1.0)
                  AND ms_code IS NOT NULL

            ),

            pair_votes AS (

                SELECT
                    a.undl_id,
                    a.year,
                    a.body_code,
                    a.resolution,

                    a.ms_code AS country_a,
                    b.ms_code AS country_b,

                    a.vote_score AS vote_score_a,
                    b.vote_score AS vote_score_b

                FROM votes a

                INNER JOIN votes b

                    ON a.undl_id = b.undl_id
                    AND a.year = b.year
                    AND a.body_code = b.body_code
                    AND a.resolution = b.resolution

                    -- prevents A-B and B-A duplicates
                    AND a.ms_code < b.ms_code

            ),

            scored AS (

                SELECT

                    undl_id,
                    year,
                    body_code,
                    resolution,
                    country_a,
                    country_b,

                    country_a || '-' || country_b AS pair,

                    vote_score_a,
                    vote_score_b,

                    ABS(
                        vote_score_a
                        - vote_score_b
                    ) AS absolute_divergence,

                    1.0
                    - (
                        ABS(
                            vote_score_a
                            - vote_score_b
                        ) / 2.0
                    ) AS alignment_score,

                    CASE
                        WHEN
                            vote_score_a
                            * vote_score_b > 0
                        THEN 1
                        ELSE 0
                    END AS directional_agreement

                FROM pair_votes

            )

            SELECT

                country_a,
                country_b,
                pair,
                body_code,
                year,

                COUNT(*) AS observations,

                AVG(alignment_score)
                    AS mean_alignment,

                MEDIAN(alignment_score)
                    AS median_alignment,

                STDDEV_SAMP(alignment_score)
                    AS std_alignment,

                AVG(absolute_divergence)
                    AS mean_divergence,

                AVG(directional_agreement)
                    AS directional_agreement

            FROM scored

            GROUP BY
                country_a,
                country_b,
                pair,
                body_code,
                year

            ORDER BY
                country_a,
                country_b,
                body_code,
                year

        )

        TO '{OUTPUT_FILE.as_posix()}'
        (FORMAT PARQUET, COMPRESSION ZSTD);
        """

        con.execute(query)

        count = con.execute(
            f"""
            SELECT COUNT(*)
            FROM read_parquet(
                '{OUTPUT_FILE.as_posix()}'
            )
            """
        ).fetchone()[0]

        pair_count = con.execute(
            f"""
            SELECT COUNT(DISTINCT pair)
            FROM read_parquet(
                '{OUTPUT_FILE.as_posix()}'
            )
            """
        ).fetchone()[0]

        country_count = con.execute(
            f"""
            SELECT COUNT(DISTINCT country_a)
                 + COUNT(DISTINCT country_b)
            FROM read_parquet(
                '{OUTPUT_FILE.as_posix()}'
            )
            """
        ).fetchone()[0]

        print()
        print(
            f"[OK] Analytical rows: {count:,}"
        )

        print(
            f"[OK] Country-pair combinations: "
            f"{pair_count:,}"
        )

        print(
            f"[OK] Output: {OUTPUT_FILE}"
        )

        print()
        print("SAMPLE:")

        sample = con.execute(
            f"""
            SELECT *
            FROM read_parquet(
                '{OUTPUT_FILE.as_posix()}'
            )
            LIMIT 10
            """
        ).df()

        print(
            sample.to_string(index=False)
        )

    finally:
        con.close()

    print()
    print("=" * 70)
    print("ALL-COUNTRY ALIGNMENT BUILD COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()