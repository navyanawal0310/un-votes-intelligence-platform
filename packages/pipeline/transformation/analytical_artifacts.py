from __future__ import annotations

from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[3]

GOLD_ANALYTICAL = (
    BASE_DIR / "data" / "gold" / "analytical"
)


def load_change_points() -> pd.DataFrame:
    """
    Load canonical country-pair change points.

    Source-agnostic interface:
    future event sources can expose equivalent
    analytical artifacts without changing consumers.
    """

    path = (
        GOLD_ANALYTICAL
        / "country_pair_change_points.parquet"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Change-point artifact not found: {path}"
        )

    return pd.read_parquet(path)


def load_temporal_alignment() -> pd.DataFrame:
    """Load canonical temporal country-pair alignment."""

    path = (
        GOLD_ANALYTICAL
        / "country_pair_temporal_alignment.parquet"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Temporal alignment artifact not found: {path}"
        )

    return pd.read_parquet(path)


def load_country_pair_alignment() -> pd.DataFrame:
    """Load canonical annual country-pair alignment."""

    path = (
        GOLD_ANALYTICAL
        / "country_pair_alignment.parquet"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Country-pair alignment artifact not found: {path}"
        )

    return pd.read_parquet(path)