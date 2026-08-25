"""
Public country-pair analytical query interface.

Keeps callers independent of the underlying analytical
artifacts and storage format.
"""

from __future__ import annotations

from typing import Any

from packages.analytics.country_pair_report import (
    build_country_pair_report,
)


def query_country_pair(
    country_a: str,
    country_b: str,
) -> dict[str, Any]:
    """
    Return the complete intelligence report for a
    country pair.

    The interface is intentionally source-agnostic:
    future evidence sources can be incorporated into
    the report without changing the caller contract.
    """

    country_a = country_a.strip().upper()
    country_b = country_b.strip().upper()

    if not country_a or not country_b:
        raise ValueError(
            "Both country codes are required."
        )

    if country_a == country_b:
        raise ValueError(
            "Country pair must contain two different countries."
        )

    return build_country_pair_report(
        country_a,
        country_b,
    )