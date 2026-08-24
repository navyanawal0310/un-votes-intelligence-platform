"""
Canonical country-pair utilities.

All country-pair logic should use this module rather than
constructing pair strings independently throughout the project.
"""

from __future__ import annotations


def canonical_pair(
    country_a: str,
    country_b: str,
) -> str:
    """
    Return the canonical representation of a country pair.

    Country ordering is deterministic and case-insensitive.

    Examples
    --------
    >>> canonical_pair("IND", "CHN")
    'CHN-IND'

    >>> canonical_pair("chn", "ind")
    'CHN-IND'

    >>> canonical_pair("IND", "IND")
    ValueError
    """

    a = str(country_a).strip().upper()
    b = str(country_b).strip().upper()

    if not a or not b:
        raise ValueError(
            "Country codes must not be empty."
        )

    if a == b:
        raise ValueError(
            "A country pair cannot contain the same country twice."
        )

    return "-".join(sorted((a, b)))