from __future__ import annotations

import duckdb
import pandas as pd


def temporal_alignment(
    alignment: pd.DataFrame,
    window: int = 5,
    min_observations: int = 3,
) -> pd.DataFrame:
    """
    Calculate rolling temporal alignment from annual
    country-pair alignment summaries.

    Annual alignment is weighted by the number of
    underlying voting observations.

    This preserves the statistical information from
    the Gold analytical layer rather than treating a
    year with 4 votes as equivalent to a year with 150 votes.
    """

    if alignment.empty:
        return pd.DataFrame()

    if window < 1:
        raise ValueError("window must be >= 1")

    required = {
        "country_a",
        "country_b",
        "year",
        "observations",
        "mean_alignment",
        "mean_divergence",
        "directional_agreement",
    }

    missing = required - set(alignment.columns)

    if missing:
        raise ValueError(
            f"Temporal alignment missing required columns: "
            f"{sorted(missing)}"
        )

    df = alignment.copy()

    numeric_columns = [
        "year",
        "observations",
        "mean_alignment",
        "mean_divergence",
        "directional_agreement",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.dropna(
        subset=numeric_columns
    )

    df["year"] = df["year"].astype(int)
    df["observations"] = df["observations"].astype(int)

    df = df[
        df["observations"] > 0
    ].copy()

    if df.empty:
        return pd.DataFrame()

    con = duckdb.connect()

    try:

        con.register(
            "annual_alignment",
            df,
        )

        query = f"""
        WITH yearly AS (

            SELECT
                country_a,
                country_b,
                year,
                observations,
                mean_alignment,
                mean_divergence,
                directional_agreement

            FROM annual_alignment

        ),

        windows AS (

            SELECT

                country_a,
                country_b,

                year AS window_end,

                year - {window - 1}
                    AS window_start,

                SUM(observations) OVER (
                    PARTITION BY
                        country_a,
                        country_b
                    ORDER BY year
                    RANGE BETWEEN
                        {window - 1} PRECEDING
                        AND CURRENT ROW
                ) AS observations,

                SUM(
                    mean_alignment
                    * observations
                ) OVER (
                    PARTITION BY
                        country_a,
                        country_b
                    ORDER BY year
                    RANGE BETWEEN
                        {window - 1} PRECEDING
                        AND CURRENT ROW
                )
                /
                NULLIF(
                    SUM(observations) OVER (
                        PARTITION BY
                            country_a,
                            country_b
                        ORDER BY year
                        RANGE BETWEEN
                            {window - 1} PRECEDING
                            AND CURRENT ROW
                    ),
                    0
                ) AS mean_alignment,

                SUM(
                    mean_divergence
                    * observations
                ) OVER (
                    PARTITION BY
                        country_a,
                        country_b
                    ORDER BY year
                    RANGE BETWEEN
                        {window - 1} PRECEDING
                        AND CURRENT ROW
                )
                /
                NULLIF(
                    SUM(observations) OVER (
                        PARTITION BY
                            country_a,
                            country_b
                        ORDER BY year
                        RANGE BETWEEN
                            {window - 1} PRECEDING
                            AND CURRENT ROW
                    ),
                    0
                ) AS mean_divergence,

                SUM(
                    directional_agreement
                    * observations
                ) OVER (
                    PARTITION BY
                        country_a,
                        country_b
                    ORDER BY year
                    RANGE BETWEEN
                        {window - 1} PRECEDING
                        AND CURRENT ROW
                )
                /
                NULLIF(
                    SUM(observations) OVER (
                        PARTITION BY
                            country_a,
                            country_b
                        ORDER BY year
                        RANGE BETWEEN
                            {window - 1} PRECEDING
                            AND CURRENT ROW
                    ),
                    0
                ) AS directional_agreement

            FROM yearly
        )

        SELECT
            country_a,
            country_b,
            window_start,
            window_end,
            observations,
            mean_alignment,
            mean_divergence,
            directional_agreement

        FROM windows

        WHERE observations >= {min_observations}

        ORDER BY
            country_a,
            country_b,
            window_end
        """

        result = con.execute(
            query
        ).df()

    finally:
        con.close()

    return result