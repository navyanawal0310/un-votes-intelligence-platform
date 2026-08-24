from __future__ import annotations

from pathlib import Path

import pandas as pd

from packages.pipeline.contracts.validate import (
    validate_canonical_schema,
)


def write_silver(
    df: pd.DataFrame,
    output_path: Path,
) -> Path:
    """
    Validate and persist a canonical dataset to Silver.
    """

    validate_canonical_schema(df)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_parquet(
        output_path,
        index=False,
    )

    return output_path


def read_silver(
    path: Path,
) -> pd.DataFrame:
    """
    Load a validated Silver dataset.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Silver dataset not found: {path}"
        )

    df = pd.read_parquet(path)

    validate_canonical_schema(df)

    return df