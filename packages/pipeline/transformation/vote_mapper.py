"""
Vote normalization utilities.

Provides both:
1. Rich VoteInfo objects for business logic.
2. Fast lookup dictionaries for vectorized ETL.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class VoteInfo:
    """
    Represents a normalized UN vote.
    """

    code: str
    label: str
    score: int | None


VOTE_MAPPING: Final[dict[str, VoteInfo]] = {
    "Y": VoteInfo("Y", "YES", 1),
    "N": VoteInfo("N", "NO", -1),
    "A": VoteInfo("A", "ABSTAIN", 0),
    "X": VoteInfo("X", "ABSENT", None),
}

# ----------------------------------------------------------------------
# Fast lookup dictionaries for pandas vectorized operations
# ----------------------------------------------------------------------

VOTE_LABEL_MAP: Final[dict[str, str]] = {
    code: vote.label
    for code, vote in VOTE_MAPPING.items()
}

VOTE_SCORE_MAP: Final[dict[str, int | None]] = {
    code: vote.score
    for code, vote in VOTE_MAPPING.items()
}


def map_vote(vote_code: str) -> VoteInfo:
    """
    Map a raw UN vote code to a VoteInfo object.
    """

    vote_code = vote_code.strip().upper()

    try:
        return VOTE_MAPPING[vote_code]
    except KeyError as exc:
        raise ValueError(
            f"Unknown vote code: '{vote_code}'"
        ) from exc