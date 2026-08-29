from __future__ import annotations

from fastapi import APIRouter, HTTPException

from packages.analytics.relationship_intelligence import (
    relationship_profile,
)
from packages.analytics.query import execute_query
from packages.api.schemas import (
    QueryRequest,
    QueryResponse,
    RelationshipResponse,
)

router = APIRouter(
    prefix="/api/v1",
)


@router.get(
    "/relationship/{country_a}/{country_b}",
    response_model=RelationshipResponse,
)
def get_relationship(
    country_a: str,
    country_b: str,
):
    country_a = country_a.upper()
    country_b = country_b.upper()

    try:
        result = relationship_profile(
            country_a,
            country_b,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Relationship profile not found",
        )

    return {
        "pair": result.get(
            "pair",
            f"{country_a}-{country_b}",
        ),
        "country_a": result.get(
            "country_a",
            country_a,
        ),
        "country_b": result.get(
            "country_b",
            country_b,
        ),
        "relationship_score": result.get(
            "relationship_score"
        ),
        "relationship_direction": result.get(
            "relationship_direction"
        ),
        "evidence_source": result.get(
            "evidence_source",
            "UN_VOTING",
        ),
        "provenance": result.get(
            "provenance",
            "UN_VOTES_ANALYZER",
        ),
        "evidence": (
            result.get("evidence")
            if isinstance(result.get("evidence"), dict)
            else {
                "temporal_alignment": result.get(
                    "temporal_alignment", 0
                ),
                "change_points": result.get(
                    "change_points", 0
                ),
                "issue_attribution": result.get(
                    "issue_attribution", 0
                ),
                "episode_attribution": result.get(
                    "episode_attribution", 0
                ),
            }
        ),
    }


@router.post(
    "/query",
    response_model=QueryResponse,
)
def query_intelligence(
    request: QueryRequest,
):
    try:
        result = execute_query(
            request.question,
            request.country_a.upper(),
            request.country_b.upper(),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "question": result["question"],
        "intent": result["intent"],
        "answer": result["answer"],
        "evidence": (
            result.get("result", {}).get(
                "evidence_summary"
            )
            if isinstance(result.get("result"), dict)
            else None
        ),
        "evidence_source": result["evidence_source"],
        "provenance": result["provenance"],
    }