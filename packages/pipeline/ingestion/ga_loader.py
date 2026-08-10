"""
General Assembly dataset loader.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from packages.pipeline.transformation.canonical import normalize_votes


REQUIRED_COLUMNS = {
    "undl_id",
    "ms_code",
    "ms_name",
    "ms_vote",
    "date",
    "session",
    "resolution",
    "meeting",
    "title",
    "total_yes",
    "total_no",
    "total_abstentions",
    "total_non_voting",
    "total_ms",
    "undl_link",
}


def load_ga_dataset(path: Path) -> pd.DataFrame:
    """Load and normalize the official UN General Assembly dataset."""

    df = pd.read_csv(path)

    missing = REQUIRED_COLUMNS - set(df.columns)

    if missing:
        raise ValueError(
            f"GA dataset is missing required columns: {sorted(missing)}"
        )

    return normalize_votes(df, body_code="GA")