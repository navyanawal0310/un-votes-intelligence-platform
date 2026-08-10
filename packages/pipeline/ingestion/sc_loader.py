"""
Security Council dataset loader.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from packages.pipeline.transformation.canonical import normalize_votes


REQUIRED_COLUMNS = {
    "undl_id",
    "ms_code",
    "ms_name",
    "permanent_member",
    "ms_vote",
    "date",
    "resolution",
    "meeting",
    "description",
    "total_yes",
    "total_no",
    "total_abstentions",
    "total_non_voting",
    "total_ms",
    "modality",
    "undl_link",
}


def load_sc_dataset(path: Path) -> pd.DataFrame:
    """Load and normalize the official UN Security Council dataset."""

    df = pd.read_csv(path)

    missing = REQUIRED_COLUMNS - set(df.columns)

    if missing:
        raise ValueError(
            f"SC dataset is missing required columns: {sorted(missing)}"
        )

    return normalize_votes(df, body_code="SC")