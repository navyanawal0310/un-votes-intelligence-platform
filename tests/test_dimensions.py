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


df = load_dataset(DOWNLOADS_DIR / DATASET_FILENAME)
long_df = unpivot_dataset(df)

dim_council = build_dim_council(long_df)
dim_date = build_dim_date(long_df)
dim_country = build_dim_country(long_df)
dim_resolution = build_dim_resolution(long_df)
print("COUNCIL DIMENSION:")
print(dim_council)

print("\nDATE DIMENSION:")
print(dim_date.head())

print("\nCOUNTRY DIMENSION")
print("-" * 40)
print(dim_country.head(20))

print()
print(f"Countries: {len(dim_country):,}")

print("\nDATE DIMENSION INFO:")
dim_date.info()
year_only_dates = dim_date[
    dim_date["date_precision"] == "YEAR_ONLY"
]

print("\nYEAR-ONLY DATES")
print(year_only_dates)

assert dim_date["date_id"].is_unique
assert dim_date["year"].notna().all()
assert dim_date["date_precision"].isin(
    ["FULL_DATE", "YEAR_ONLY"]
).all()

print("\nDate dimension validation: PASSED")

print("\nCOUNTRY NORMALIZATION AUDIT")
print("-" * 50)

country_audit = (
    long_df[["CountryRaw", "Country"]]
    .drop_duplicates()
    .sort_values(["Country", "CountryRaw"])
)

normalized_duplicates = (
    country_audit[
        country_audit["Country"].duplicated(keep=False)
    ]
)

print("Raw country names:", country_audit["CountryRaw"].nunique())
print("Canonical countries:", country_audit["Country"].nunique())

print("\nCOUNTRY NAMES WITH MULTIPLE SOURCE REPRESENTATIONS:")
print(normalized_duplicates.to_string(index=False))
assert dim_country["country_id"].is_unique
assert dim_country["country_name"].is_unique
assert dim_country["country_name"].notna().all()
assert (
    dim_country["country_name"].str.strip()
    == dim_country["country_name"]
).all()
print("\nCOUNTRY DIMENSION VALIDATION: PASSED")
problematic = country_audit[
    country_audit["CountryRaw"].str.contains(
        r"^(?:\s+|\s*Aa\s+|\s*AY\s+)",
        regex=True,
        na=False,
    )
]

print("\nNORMALIZED SOURCE VALUES:")
print(problematic.to_string(index=False))

print("\nRESOLUTION DIMENSION")
print("-" * 50)
print(dim_resolution.head(20).to_string(index=False))

print()
print(f"Resolutions: {len(dim_resolution):,}")

assert dim_resolution["resolution_id"].is_unique
assert dim_resolution["resolution_code"].is_unique
assert dim_resolution["resolution_code"].notna().all()

print("\nResolution dimension validation: PASSED")
