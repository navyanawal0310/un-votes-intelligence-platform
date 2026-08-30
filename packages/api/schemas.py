from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str

class RelationshipResponse(BaseModel):
    pair: str
    country_a: str
    country_b: str

    latest_year: int | None = None

    relationship_score: float | None = None
    relationship_direction: str | None = None

    alignment: float | None = None
    divergence: float | None = None
    directional_agreement: float | None = None

    evidence_count: int = 0
    change_episode_count: int = 0
    confirmed_episode_count: int = 0
    change_points: int = 0
    relationship_rows: int = 0

    evidence_source: str | None = None
    provenance: str | None = None

    evidence: dict[str, int] | None = None

    substantive_intelligence: dict | list | None = None
    external_evidence: list | None = None

class QueryRequest(BaseModel):
    question: str
    country_a: str
    country_b: str

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Query question cannot be empty.")
        return value


class QueryResponse(BaseModel):
    question: str
    intent: str
    answer: str
    evidence: dict | None = None
    evidence_source: str
    provenance: str