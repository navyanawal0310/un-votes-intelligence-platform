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
    """
    Load and normalize the official UN General Assembly dataset.

    The loader performs:
        1. Raw CSV ingestion
        2. Schema verification
        3. Deterministic session normalization
        4. Session-number extraction
        5. Canonical vote normalization
    """

    # --------------------------------------------------------
    # Validate input path
    # --------------------------------------------------------

    if not path.exists():
        raise FileNotFoundError(
            f"General Assembly dataset not found: {path}"
        )

    # --------------------------------------------------------
    # Read with explicit types
    #
    # session and vote_note are textual fields.
    # Explicit dtype prevents Pandas mixed-type inference.
    # --------------------------------------------------------

    df = pd.read_csv(
        path,
        dtype={
            "session": "string",
            "vote_note": "string",
        },
    )

    # --------------------------------------------------------
    # Schema validation
    # --------------------------------------------------------

    missing = REQUIRED_COLUMNS - set(df.columns)

    if missing:
        raise ValueError(
            "GA dataset is missing required columns: "
            f"{sorted(missing)}"
        )

    # --------------------------------------------------------
    # Normalize session
    # --------------------------------------------------------

    df["session"] = (
        df["session"]
        .astype("string")
        .str.strip()
    )

    # --------------------------------------------------------
    # Extract numeric session number
    # --------------------------------------------------------

    df["session_number"] = (
        df["session"]
        .str.extract(
            r"^(\d+)",
            expand=False,
        )
        .astype("Int64")
    )

    # --------------------------------------------------------
    # Canonical transformation
    # --------------------------------------------------------

    return normalize_votes(
        df,
        body_code="GA",
    )