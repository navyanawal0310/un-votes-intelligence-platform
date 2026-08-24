"""
Country-pair registry construction.
"""

from __future__ import annotations

import pandas as pd

from packages.common.country_pairs import canonical_pair


def build_country_pair_registry(
    countries: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build the canonical country-pair registry.

    Parameters
    ----------
    countries:
        DataFrame containing:

        country_id
        ms_code

    Returns
    -------
    pandas.DataFrame
        Canonical country-pair registry.
    """

    required_columns = {
        "country_id",
        "ms_code",
    }

    missing = required_columns.difference(
        countries.columns
    )

    if missing:
        raise ValueError(
            "Missing required country columns: "
            f"{sorted(missing)}"
        )

    records = []

    rows = list(
        countries[
            ["country_id", "ms_code"]
        ].itertuples(index=False)
    )

    for country_a, country_b in (
        (rows[i], rows[j])
        for i in range(len(rows))
        for j in range(i + 1, len(rows))
    ):

        country_a_id = int(country_a.country_id)
        country_b_id = int(country_b.country_id)

        country_a_code = str(
            country_a.ms_code
        ).strip().upper()

        country_b_code = str(
            country_b.ms_code
        ).strip().upper()

        # ----------------------------------------------------
        # Canonical ordering must be based on country IDs.
        # ----------------------------------------------------

        if country_a_id > country_b_id:

            country_a_id, country_b_id = (
                country_b_id,
                country_a_id,
            )

            country_a_code, country_b_code = (
                country_b_code,
                country_a_code,
            )

        records.append(
            {
                "country_a_id": country_a_id,
                "country_b_id": country_b_id,
                "canonical_pair": canonical_pair(
                    country_a_code,
                    country_b_code,
                ),
            }
        )

    result = pd.DataFrame(records)

    if result.empty:
        return pd.DataFrame(
            columns=[
                "pair_id",
                "country_a_id",
                "country_b_id",
                "canonical_pair",
            ]
        )

    result.insert(
        0,
        "pair_id",
        range(1, len(result) + 1),
    )

    return result