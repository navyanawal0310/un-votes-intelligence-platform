from packages.common.constants import DATASET_FILENAME
from packages.common.paths import DOWNLOADS_DIR
from packages.pipeline.profiling.analyzer import load_dataset
from packages.pipeline.transformation.unpivot import unpivot_dataset
from packages.warehouse.dimensions import (
    build_dim_council,
    build_dim_date,
    build_dim_country,
)


df = load_dataset(DOWNLOADS_DIR / DATASET_FILENAME)
long_df = unpivot_dataset(df)

dim_council = build_dim_council(long_df)
dim_date = build_dim_date(long_df)
dim_country = build_dim_country(long_df)

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

assert dim_date["date_id"].is_unique
assert dim_date["full_date"].is_unique
assert dim_date["full_date"].notna().all()

print("\nDate dimension validation: PASSED")
