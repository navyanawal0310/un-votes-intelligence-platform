from pathlib import Path

import pandas as pd

from apps.api.app.database.warehouse import WarehouseLoader


DATABASE_PATH = Path(
    "data/warehouse/un_votes.duckdb"
)


df = pd.DataFrame(
    {
        "id": [1, 2, 3],
        "name": [
            "India",
            "USA",
            "Japan",
        ],
    }
)


loader = WarehouseLoader(
    DATABASE_PATH
)

loader.load_dataframe(
    df,
    "test_table",
)

result = loader.query(
    "SELECT * FROM test_table"
)

print(result)

loader.close()

print("\nDuckDB warehouse loader: PASSED")