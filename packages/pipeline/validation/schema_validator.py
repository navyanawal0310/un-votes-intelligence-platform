"""
Schema validation for the UN voting dataset.
"""

from __future__ import annotations

import pandas as pd

from packages.common.constants import METADATA_COLUMNS
from packages.pipeline.validation.models import SchemaValidationResult
from packages.pipeline.validation.exceptions import SchemaValidationError


class SchemaValidator:
    """
    Validates the structure of the UN voting dataset.
    """

    def validate(self, df: pd.DataFrame) -> SchemaValidationResult:

        errors: list[str] = []

        columns = df.columns.tolist()

        # ------------------------------------------------------------------
        # Required metadata columns
        # ------------------------------------------------------------------

        missing_metadata = [
            column
            for column in METADATA_COLUMNS
            if column not in columns
        ]

        if missing_metadata:
            errors.append(
                f"Missing metadata columns: {missing_metadata}"
            )

        # ------------------------------------------------------------------
        # Duplicate columns
        # ------------------------------------------------------------------

        duplicate_columns = df.columns[df.columns.duplicated()].tolist()

        if duplicate_columns:
            errors.append(
                f"Duplicate columns detected: {duplicate_columns}"
            )

        # ------------------------------------------------------------------
        # Empty column names
        # ------------------------------------------------------------------

        empty_columns = [
            column
            for column in columns
            if str(column).strip() == ""
        ]

        if empty_columns:
            errors.append("Dataset contains empty column names.")

        # ------------------------------------------------------------------
        # Country columns
        # ------------------------------------------------------------------

        country_columns = [
            column
            for column in columns
            if column not in METADATA_COLUMNS
        ]

        if not country_columns:
            errors.append(
                "No country columns detected."
            )

        return SchemaValidationResult(
            is_valid=len(errors) == 0,
            metadata_columns=METADATA_COLUMNS,
            country_columns=country_columns,
            errors=errors,
        )

    @staticmethod
    def raise_if_invalid(
        result: SchemaValidationResult,
    ) -> None:
        """
        Raise SchemaValidationError if validation failed.
        """

        if not result.is_valid:
            raise SchemaValidationError(
                "\n".join(result.errors)
            )