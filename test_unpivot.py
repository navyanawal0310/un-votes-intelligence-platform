from packages.common.constants import DATASET_FILENAME
from packages.common.paths import DOWNLOADS_DIR
from packages.pipeline.profiling.analyzer import load_dataset
from packages.pipeline.transformation.unpivot import unpivot_dataset

DATASET_PATH = DOWNLOADS_DIR / DATASET_FILENAME

df = load_dataset(DATASET_PATH)

long_df = unpivot_dataset(df)

print(long_df.head())

print()

print(f"Rows before : {len(df):,}")
print(f"Rows after  : {len(long_df):,}")
print(f"Columns     : {len(long_df.columns)}")