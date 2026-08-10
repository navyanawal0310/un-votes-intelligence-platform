"""
Canonical schema for UN voting records.
"""

from __future__ import annotations

import pandas as pd

from packages.pipeline.transformation.vote_mapper import (
    normalize_vote_code,
    VOTE_LABEL_MAP,
    VOTE_SCORE_MAP,
)


COMMON_COLUMNS = [
    "undl_id",
    "ms_code",
    "ms_name",
    "ms_vote",
    "date",
    "resolution",
    "draft",
    "meeting",
    "subjects",
    "vote_note",
    "total_yes",
    "total_no",
    "total_abstentions",
    "total_non_voting",
    "total_ms",
    "undl_link",
]


def normalize_votes(
    df: pd.DataFrame,
    body_code: str,
) -> pd.DataFrame:
    """
    Convert an official UN voting dataset into the
    platform's canonical voting schema.
    """

    result = df.copy()

    result["body_code"] = body_code

    result["ms_vote"] = result["ms_vote"].map(normalize_vote_code)

    result["vote_code"] = result["ms_vote"]

    result["vote_label"] = result["vote_code"].map(VOTE_LABEL_MAP)

    result["vote_score"] = result["vote_code"].map(VOTE_SCORE_MAP)

    result["date"] = pd.to_datetime(
        result["date"],
        errors="coerce",
    )

    return result