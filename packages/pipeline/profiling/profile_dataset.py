"""
Entry point for dataset profiling.
"""

from .analyzer import load_dataset, profile_dataset
from .exporters import ProfileExporter

from packages.common.constants import DATASET_FILENAME
from packages.common.paths import DOWNLOADS_DIR
from packages.pipeline.validation.schema_validator import SchemaValidator

DATASET_PATH = DOWNLOADS_DIR / DATASET_FILENAME


def main() -> None:
    # ------------------------------------------------------------------
    # Load dataset
    # ------------------------------------------------------------------

    df = load_dataset(DATASET_PATH)

    # ------------------------------------------------------------------
    # Validate schema
    # ------------------------------------------------------------------

    validator = SchemaValidator()

    validation = validator.validate(df)

    validator.raise_if_invalid(validation)

    # ------------------------------------------------------------------
    # Profile dataset
    # ------------------------------------------------------------------

    profile = profile_dataset(df)

    # ------------------------------------------------------------------
    # Console summary
    # ------------------------------------------------------------------

    print("\nUN DATASET PROFILE")
    print("-" * 60)

    print(f"Rows              : {profile.rows:,}")
    print(f"Columns           : {profile.columns}")
    print(f"Metadata Columns  : {len(profile.metadata_columns)}")
    print(f"Country Columns   : {len(profile.country_columns)}")
    print(f"Duplicate Rows    : {profile.duplicate_rows}")
    print(f"Memory Usage (MB) : {profile.memory_usage_mb:.2f}")

    print("-" * 60)

    # ------------------------------------------------------------------
    # Export reports
    # ------------------------------------------------------------------

    exporter = ProfileExporter()

    exporter.export(profile)

    print("Reports exported successfully.")


if __name__ == "__main__":
    main()