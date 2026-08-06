"""
Domain models used during ETL transformation.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class VoteRecord:
    """
    Represents one country's vote on one resolution.
    """

    council: str
    date: datetime
    title: str
    resolution: str

    country: str
    vote: str

    total_votes: Optional[int]
    yes_count: Optional[int]
    no_count: Optional[int]
    absent_count: Optional[int]
    no_vote_count: Optional[int]

    source_link: str
    token: str


@dataclass(slots=True)
class TransformationResult:
    """
    Summary of transformation.
    """

    rows_before: int
    rows_after: int

    countries_processed: int

    rejected_records: int