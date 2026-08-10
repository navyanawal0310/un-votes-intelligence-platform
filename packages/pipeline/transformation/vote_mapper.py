"""
UN vote normalization utilities.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VoteInfo:
    code: str
    label: str
    score: int | None


VOTE_MAPPING = {
    "Y": VoteInfo("Y", "YES", 1),
    "N": VoteInfo("N", "NO", -1),
    "A": VoteInfo("A", "ABSTAIN", 0),
    "X": VoteInfo("X", "ABSENT", None),
}


VOTE_LABEL_MAP = {
    code: info.label
    for code, info in VOTE_MAPPING.items()
}


VOTE_SCORE_MAP = {
    code: info.score
    for code, info in VOTE_MAPPING.items()
}


VALID_VOTE_CODES = frozenset(VOTE_MAPPING)


def normalize_vote_code(vote: str) -> str:
    """
    Normalize a raw UN vote code.

    Parameters
    ----------
    vote:
        Raw vote value from the UN dataset.

    Returns
    -------
    str
        Normalized vote code.

    Raises
    ------
    ValueError
        If the vote code is not recognized.
    """

    code = str(vote).strip().upper()

    if code not in VALID_VOTE_CODES:
        raise ValueError(f"Unknown UN vote code: {vote!r}")

    return code