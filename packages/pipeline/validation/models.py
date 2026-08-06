"""
Validation models.
"""

from dataclasses import dataclass


@dataclass(slots=True)
class SchemaValidationResult:
    """
    Result of schema validation.
    """

    is_valid: bool
    metadata_columns: list[str]
    country_columns: list[str]
    errors: list[str]