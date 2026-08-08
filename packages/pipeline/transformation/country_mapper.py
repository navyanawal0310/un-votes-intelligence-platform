"""
Country-name normalization for the UN voting dataset.

Keeps source country names traceable while providing a canonical
country name for downstream warehouse dimensions.
"""

from __future__ import annotations

import re


# Explicit mappings for known malformed/legacy source values.
COUNTRY_NAME_MAPPING: dict[str, str] = {
    "Aa UNITED STATES": "UNITED STATES",
    "AY DENMARK": "DENMARK",
    "AY SWEDEN": "SWEDEN",
    "AY UNION OF SOUTH AFRICA": "UNION OF SOUTH AFRICA",
}


def normalize_country_name(country: str) -> str:
    """
    Normalize a country name from the raw UN dataset.

    Parameters
    ----------
    country:
        Raw country column name.

    Returns
    -------
    str
        Canonical country name.
    """

    if not isinstance(country, str):
        raise TypeError(
            f"Country name must be a string, got {type(country).__name__}"
        )

    normalized = country.strip()

    if normalized in COUNTRY_NAME_MAPPING:
        return COUNTRY_NAME_MAPPING[normalized]

    return normalized


def is_suspicious_country_name(country: str) -> bool:
    """
    Identify country names that may require manual review.

    This does not modify the value.
    """

    return bool(
        re.match(r"^(AA|Aa|AY|Ay)\s+", country.strip())
    )