"""
Entry point for dataset profiling.
"""

from pathlib import Path

from .analyzer import load_dataset, profile_dataset

DATASET_PATH = Path("data/raw/downloads/UN DATA.csv")


def main() -> None:

    df = load_dataset(DATASET_PATH)

    profile = profile_dataset(df)

    print("\nUN DATASET PROFILE")
    print("-" * 60)

    print(f"Rows              : {profile.rows:,}")
    print(f"Columns           : {profile.columns}")
    print(f"Metadata Columns  : {len(profile.metadata_columns)}")
    print(f"Country Columns   : {len(profile.country_columns)}")
    print(f"Duplicate Rows    : {profile.duplicate_rows}")
    print(f"Memory Usage (MB) : {profile.memory_usage_mb:.2f}")

    print("-" * 60)


if __name__ == "__main__":
    main()