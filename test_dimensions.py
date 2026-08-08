from packages.common.constants import DATASET_FILENAME
from packages.common.paths import DOWNLOADS_DIR
from packages.pipeline.profiling.analyzer import load_dataset
from packages.pipeline.transformation.unpivot import unpivot_dataset
from packages.warehouse.dimensions import (
    build_dim_council,
    build_dim_date,
)


df = load_dataset(DOWNLOADS_DIR / DATASET_FILENAME)
long_df = unpivot_dataset(df)

dim_council = build_dim_council(long_df)
dim_date = build_dim_date(long_df)

print("COUNCIL DIMENSION:")
print(dim_council)

print("\nDATE DIMENSION:")
print(dim_date.head())

print("\nDATE DIMENSION INFO:")
print(dim_date.info())