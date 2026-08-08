from packages.common.constants import DATASET_FILENAME
from packages.common.paths import DOWNLOADS_DIR
from packages.pipeline.profiling.analyzer import load_dataset
from packages.pipeline.transformation.unpivot import unpivot_dataset
from packages.warehouse_builder.councils import (
    build_council_dimension,
)

df = load_dataset(DOWNLOADS_DIR / DATASET_FILENAME)
long_df = unpivot_dataset(df)

dimension = build_council_dimension(long_df)

print(dimension)