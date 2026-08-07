import pandas as pd

from packages.pipeline.loader.warehouse_loader import (
    WarehouseLoader,
)

loader = WarehouseLoader()

df = pd.DataFrame(
    {
        "id": [1, 2, 3],
        "name": ["India", "USA", "Japan"],
    }
)

loader.load_dataframe(
    df,
    "test_table",
    if_exists="replace",
)

print(
    loader.query(
        "SELECT * FROM test_table"
    )
)

loader.close()