from __future__ import annotations

from fastapi import APIRouter, HTTPException
from analytical_pipeline import (
    available_countries,
    load_pipeline,
)
from packages.analytics.relationship_intelligence import (
    relationship_profile,
    relationship_history,
    relationship_changes,
)

from packages.analytics.query import (
    execute_query,
    query_country_pair,
)

from packages.api.schemas import (
    QueryRequest,
    QueryResponse,
    RelationshipResponse,
)
import math
import numpy as np
import pandas as pd

def _json_safe(value):
    """
    Convert analytical objects into JSON-safe native Python values.

    Keeps the analytics layer rich while making the API transport-safe.
    """
    if isinstance(value, pd.DataFrame):
        return [
            _json_safe(row)
            for row in value.to_dict(orient="records")
        ]

    if isinstance(value, pd.Series):
        return _json_safe(value.to_dict())

    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())

    if isinstance(value, np.generic):
        return _json_safe(value.item())

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if isinstance(value, dict):
        return {
            str(key): _json_safe(val)
            for key, val in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            _json_safe(item)
            for item in value
        ]

    if isinstance(value, float):
        if not math.isfinite(value):
            return None

    return value

router = APIRouter(
    prefix="/api/v1",
)

@router.get("/countries")
def get_countries():
    pipeline = load_pipeline()

    countries = available_countries(
        pipeline
    )

    return {
        "countries": countries,
        "count": len(countries),
    }
    

@router.get(
    "/relationship/{country_a}/{country_b}",
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

    return _json_safe(result)

@router.get(
    "/relationship/{country_a}/{country_b}/history"
)
def get_relationship_history(
    country_a: str,
    country_b: str,
):
    try:
        history = relationship_history(
            country_a.upper(),
            country_b.upper(),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return _json_safe({
        "pair": f"{country_a.upper()}-{country_b.upper()}",
        "history": history.to_dict(
            orient="records"
        ),
    })

@router.get(
    "/relationship/{country_a}/{country_b}/changes"
)
def get_relationship_changes(
    country_a: str,
    country_b: str,
):
    try:
        changes = relationship_changes(
            country_a.upper(),
            country_b.upper(),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return _json_safe({
        "pair": f"{country_a.upper()}-{country_b.upper()}",
        "changes": changes.to_dict(
            orient="records"
        ),
    })

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

    return _json_safe({
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
    })