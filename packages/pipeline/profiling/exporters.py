"""
Export profiling results to disk.

This module is responsible only for writing profiling outputs.
No analysis or business logic should exist here.
"""

from pathlib import Path

import pandas as pd

from packages.common.constants import (
    COUNTRY_COLUMNS_FILENAME,
    CSV_SEPARATOR,
    METADATA_COLUMNS_FILENAME,
    PROFILE_REPORT_FILENAME,
    UNIQUE_VOTE_VALUES_FILENAME,
)
from packages.common.paths import PROFILING_REPORT_DIR
from packages.pipeline.profiling.models import DatasetProfile


class ProfileExporter:
    """
    Exports profiling results into markdown and CSV reports.
    """

    def __init__(self, output_dir: Path = PROFILING_REPORT_DIR) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(self, profile: DatasetProfile) -> None:
        """
        Export all profiling outputs.
        """
        self._export_markdown(profile)
        self._export_country_columns(profile)
        self._export_metadata_columns(profile)
        self._export_unique_vote_values(profile)

    def _export_markdown(self, profile: DatasetProfile) -> None:
        """
        Generate the profiling markdown report.
        """

        report_path = self.output_dir / PROFILE_REPORT_FILENAME

        with report_path.open("w", encoding="utf-8") as file:

            file.write("# UN Dataset Profile\n\n")

            file.write("## Dataset Summary\n\n")

            file.write(f"- Rows: **{profile.rows:,}**\n")
            file.write(f"- Columns: **{profile.columns}**\n")
            file.write(
                f"- Metadata Columns: **{len(profile.metadata_columns)}**\n"
            )
            file.write(
                f"- Country Columns: **{len(profile.country_columns)}**\n"
            )
            file.write(
                f"- Duplicate Rows: **{profile.duplicate_rows}**\n"
            )
            file.write(
                f"- Memory Usage: **{profile.memory_usage_mb:.2f} MB**\n\n"
            )

            file.write("## Missing Values\n\n")

            file.write("| Column | Missing |\n")
            file.write("|--------|---------|\n")

            for column, value in profile.missing_values.items():
                file.write(f"| {column} | {value} |\n")

            file.write("\n")

            file.write("## Data Types\n\n")

            file.write("| Column | Type |\n")
            file.write("|--------|------|\n")

            for column, dtype in profile.dtypes.items():
                file.write(f"| {column} | {dtype} |\n")

    def _export_country_columns(self, profile: DatasetProfile) -> None:
        """
        Export detected country columns.
        """

        path = self.output_dir / COUNTRY_COLUMNS_FILENAME

        pd.Series(
            profile.country_columns,
            name="country_column",
        ).to_csv(
            path,
            index=False,
            sep=CSV_SEPARATOR,
        )

    def _export_metadata_columns(self, profile: DatasetProfile) -> None:
        """
        Export metadata columns.
        """

        path = self.output_dir / METADATA_COLUMNS_FILENAME

        pd.Series(
            profile.metadata_columns,
            name="metadata_column",
        ).to_csv(
            path,
            index=False,
            sep=CSV_SEPARATOR,
        )

    def _export_unique_vote_values(self, profile: DatasetProfile) -> None:
        """
        Export unique vote values.
        """

        path = self.output_dir / UNIQUE_VOTE_VALUES_FILENAME

        pd.Series(
            profile.unique_vote_values,
            name="vote_value",
        ).to_csv(
            path,
            index=False,
            sep=CSV_SEPARATOR,
        )