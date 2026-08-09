from packages.common.constants import DATASET_FILENAME
from packages.common.paths import DOWNLOADS_DIR

from packages.pipeline.profiling.analyzer import load_dataset
from packages.pipeline.transformation.unpivot import unpivot_dataset

from packages.warehouse.dimensions import (
    build_dim_council,
    build_dim_date,
    build_dim_country,
    build_dim_resolution,
)

from packages.warehouse.facts import build_fact_votes


df = load_dataset(
    DOWNLOADS_DIR / DATASET_FILENAME
)

long_df = unpivot_dataset(df)

dim_council = build_dim_council(long_df)
dim_date = build_dim_date(long_df)
dim_country = build_dim_country(long_df)
dim_resolution = build_dim_resolution(long_df)

print("\nDIMENSION KEY CHECKS")
print("-" * 60)

print(
    "Duplicate resolution codes:",
    dim_resolution["resolution_code"].duplicated().sum()
)

print(
    "Duplicate council names:",
    dim_council["council_name"].duplicated().sum()
)

print(
    "Duplicate country names:",
    dim_country["country_name"].duplicated().sum()
)

print(
    "Duplicate full dates:",
    dim_date["full_date"].duplicated().sum()
)

print("\nDUPLICATE RESOLUTION CODES")
print(
    dim_resolution[
        dim_resolution["resolution_code"].duplicated(keep=False)
    ]
)

print("\nDUPLICATE COUNCILS")
print(
    dim_council[
        dim_council["council_name"].duplicated(keep=False)
    ]
)

print("\nDUPLICATE COUNTRIES")
print(
    dim_country[
        dim_country["country_name"].duplicated(keep=False)
    ]
)

print("\nDUPLICATE DATES")
print(
    dim_date[
        dim_date["full_date"].duplicated(keep=False)
    ]
)

fact_votes = build_fact_votes(
    long_df,
    dim_council,
    dim_date,
    dim_country,
    dim_resolution,
)


print("\nFACT VOTES")
print("-" * 60)

print(fact_votes.head(10).to_string(index=False))

print()
print(f"Fact rows: {len(fact_votes):,}")
print(f"Columns: {len(fact_votes.columns)}")

print("\nFACT COLUMNS")
print(fact_votes.columns.tolist())

print("\nNULL COUNTS")
print(fact_votes.isna().sum())

print("\nVOTE DISTRIBUTION")
print(fact_votes["vote_code"].value_counts(dropna=False))

print("\nFACT TABLE INFO")
fact_votes.info()

print("\nFACT TABLE VALIDATION")
print("-" * 60)

# Every fact row must have all dimension keys.
assert fact_votes["vote_event_id"].notna().all()
assert fact_votes["resolution_id"].notna().all()
assert fact_votes["country_id"].notna().all()
assert fact_votes["council_id"].notna().all()
assert fact_votes["date_id"].notna().all()

# Only valid UN vote codes are allowed.
assert fact_votes["vote_code"].isin(
    ["Y", "N", "A", "X"]
).all()

# Vote score should be NULL only for ABSENT votes.
assert fact_votes.loc[
    fact_votes["vote_code"] == "X",
    "vote_score"
].isna().all()

assert fact_votes.loc[
    fact_votes["vote_code"] != "X",
    "vote_score"
].notna().all()

# Fact grain:
# one country vote per voting event.
duplicate_grain = fact_votes.duplicated(
    subset=["vote_event_id", "country_id"]
).sum()

print(f"Duplicate event-country rows: {duplicate_grain}")

assert duplicate_grain == 0

print("Dimension key validation: PASSED")
print("Vote code validation: PASSED")
print("Vote score validation: PASSED")
print("Fact grain validation: PASSED")