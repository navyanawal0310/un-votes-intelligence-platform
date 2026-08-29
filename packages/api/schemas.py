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
    relationship_score: float | None = None
    relationship_direction: str | None = None
    evidence_source: str
    provenance: str
    evidence: dict[str, int] | None = None


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