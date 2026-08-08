"""
Country-name normalization for the UN voting dataset.

The raw UN dataset contains inconsistent whitespace and a small number
of malformed source prefixes. This module normalizes those values while
preserving the original source value separately in the transformation
layer.
"""

from __future__ import annotations

import re
import unicodedata


# Known malformed prefixes observed in the source dataset.
# These prefixes are removed only when they occur at the beginning
# of the country name.
SOURCE_PREFIX_PATTERN = re.compile(
    r"^(?:AA|Aa|AY|Ay)\s+",
)


def normalize_country_name(country: str) -> str:
    """
    Normalize a raw UN country name.

    Normalization steps:
    1. Validate input type.
    2. Normalize Unicode representation.
    3. Normalize whitespace.
    4. Remove known malformed source prefixes.
    5. Normalize whitespace again.

    Parameters
    ----------
    country:
        Raw country name from the source dataset.

    Returns
    -------
    str
        Canonical country name.
    """

    if not isinstance(country, str):
        raise TypeError(
            f"Country name must be a string, "
            f"got {type(country).__name__}"
        )

    normalized = unicodedata.normalize("NFKC", country)

    # Convert repeated/irregular whitespace into a single space.
    normalized = " ".join(normalized.split())

    # Remove known malformed source prefixes.
    normalized = SOURCE_PREFIX_PATTERN.sub(
        "",
        normalized,
    )

    # Final whitespace normalization.
    normalized = " ".join(normalized.split())

    return normalized


def is_suspicious_country_name(country: str) -> bool:
    """
    Return True when a raw country name contains a known
    malformed source prefix.

    This function does not modify the value.
    """

    if not isinstance(country, str):
        return False

    normalized = unicodedata.normalize("NFKC", country)
    normalized = " ".join(normalized.split())

    return bool(
        SOURCE_PREFIX_PATTERN.match(normalized)
    )