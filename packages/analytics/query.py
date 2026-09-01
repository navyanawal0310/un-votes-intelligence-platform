from __future__ import annotations

import re
from enum import Enum
from typing import Any
import pandas as pd
import duckdb
from packages.warehouse.database import get_connection
from packages.analytics.country_pair_report import (
    build_country_pair_report,
)
from packages.analytics.relationship_intelligence import (
    relationship_profile,
    relationship_history,
    relationship_changes,
)
from packages.analytics.substantive_intelligence import (
    substantive_pair_intelligence,
)
from packages.analytics.resolution_nlp import (
    pair_resolution_nlp,
)
from packages.analytics.subject_rankings import (
    subject_rankings,
)

from packages.analytics.subject_trends import (
    subject_trends,
)

from packages.analytics.issue_positions import (
    issue_position_summary,
)
from packages.analytics.answer_generation import (
    generate_answer,
)


class QueryIntent(str, Enum):
    RELATIONSHIP_PROFILE = "RELATIONSHIP_PROFILE"
    RELATIONSHIP_HISTORY = "RELATIONSHIP_HISTORY"
    RELATIONSHIP_CHANGES = "RELATIONSHIP_CHANGES"
    SUBSTANTIVE_DISAGREEMENT = "SUBSTANTIVE_DISAGREEMENT"
    RESOLUTION_NLP = "RESOLUTION_NLP"
    SUBJECT_TREND = "SUBJECT_TREND"
    SUBJECT_RANKING = "SUBJECT_RANKING"
    ISSUE_POSITION = "ISSUE_POSITION"


def query_country_pair(
    country_a: str,
    country_b: str,
) -> dict[str, Any]:
    """
    Return the complete intelligence report for
    a country pair.
    """

    country_a = country_a.strip().upper()
    country_b = country_b.strip().upper()

    if not country_a or not country_b:
        raise ValueError(
            "Both country codes are required."
        )

    if country_a == country_b:
        raise ValueError(
            "Country pair must contain two different countries."
        )

    return build_country_pair_report(
        country_a,
        country_b,
    )


def classify_query(
    question: str,
) -> QueryIntent:
    """
    Classify a natural-language analytical question
    into a deterministic intelligence intent.

    More specific analytical intents are evaluated before
    broader relationship intents.
    """

    if not question or not question.strip():
        raise ValueError(
            "Query question cannot be empty."
        )

    text = question.lower().strip()

    # --------------------------------------------------
    # 1. SUBJECT-SPECIFIC INTENTS
    # --------------------------------------------------

    if any(
        term in text
        for term in (
            "subject trend",
            "subject trends",
            "trend by subject",
            "trends by subject",
            "trend on subjects",
            "disagreement by subject",
        )
    ):
        return QueryIntent.SUBJECT_TREND

    if any(
        term in text
        for term in (
            "top subjects",
            "subject ranking",
            "subject rankings",
            "ranked subjects",
            "which subjects",
            "highest disagreement subjects",
            "subjects have the highest disagreement",
        )
    ):
        return QueryIntent.SUBJECT_RANKING

    # --------------------------------------------------
    # 2. ISSUE POSITION
    # --------------------------------------------------

    if any(
        term in text
        for term in (
            "issue position",
            "position on",
            "positions on",
            "issue positions",
        )
    ):
        return QueryIntent.ISSUE_POSITION

    # --------------------------------------------------
    # 3. RESOLUTION NLP
    # --------------------------------------------------

    if any(
        term in text
        for term in (
            "resolution text",
            "resolution nlp",
            "resolution similarity",
            "keywords",
            "themes",
        )
    ):
        return QueryIntent.RESOLUTION_NLP

    # --------------------------------------------------
    # 4. SUBSTANTIVE DISAGREEMENT
    # --------------------------------------------------

    if any(
        term in text
        for term in (
            "disagree",
            "disagreement",
            "different votes",
            "voting disagreement",
        )
    ):
        return QueryIntent.SUBSTANTIVE_DISAGREEMENT

    # --------------------------------------------------
    # 5. CHANGE-POINT ANALYSIS
    # --------------------------------------------------

    if any(
        term in text
        for term in (
            "change point",
            "change points",
            "relationship change",
            "relationship changes",
            "relationship change points",
            "detected changes",
            "turning point",
            "turning points",
            "largest change",
            "largest changes",
            "biggest change",
            "biggest changes",
            "most significant change",
            "most significant changes",
            "strongest change",
            "strongest changes",
            "when did",
        )
    ):
        return QueryIntent.RELATIONSHIP_CHANGES
    # --------------------------------------------------
    # 6. HISTORICAL RELATIONSHIP
    # --------------------------------------------------

    if any(
        term in text
        for term in (
            "history",
            "historical",
            "over time",
            "trajectory",
            "trend in relationship",
            "how has the relationship changed",
            "how did the relationship change",
        )
    ):
        return QueryIntent.RELATIONSHIP_HISTORY

    # --------------------------------------------------
    # 7. DEFAULT
    # --------------------------------------------------

    return QueryIntent.RELATIONSHIP_PROFILE

def parse_query(
    question: str,
    country_a: str,
    country_b: str,
) -> dict[str, Any]:
    """
    Convert a natural-language question into a
    structured analytical query.
    """

    country_a = country_a.strip().upper()
    country_b = country_b.strip().upper()

    if not country_a or not country_b:
        raise ValueError(
            "Both country codes are required."
        )

    if country_a == country_b:
        raise ValueError(
            "Country pair must contain two different countries."
        )

    intent = classify_query(question)

    return {
        "question": question.strip(),
        "intent": intent.value,
        "country_a": country_a,
        "country_b": country_b,
    }

def resolve_country(
    country: str,
    con: duckdb.DuckDBPyConnection | None = None,
) -> str:
    """
    Resolve a country name or UN/ISO-style country code
    to the canonical ms_code stored in dim_country.
    """

    if not country or not country.strip():
        raise ValueError(
            "Country cannot be empty."
        )

    value = country.strip()

    own_connection = con is None

    if con is None:
        con = get_connection()

    try:
        result = con.execute(
            """
            SELECT ms_code
            FROM dim_country
            WHERE UPPER(ms_code) = UPPER(?)
               OR UPPER(country_name) = UPPER(?)
            LIMIT 1
            """,
            [value, value],
        ).fetchone()

        if result is None:
            raise ValueError(
                f"Unknown country: {country}"
            )

        return str(result[0]).upper()

    finally:
        if own_connection:
            con.close()

def resolve_country_pair(
    country_a: str,
    country_b: str,
    con: duckdb.DuckDBPyConnection | None = None,
) -> tuple[str, str]:
    """
    Resolve two country names/codes to canonical country codes.
    """

    country_a = resolve_country(
        country_a,
        con,
    )

    country_b = resolve_country(
        country_b,
        con,
    )

    if country_a == country_b:
        raise ValueError(
            "Country pair must contain two different countries."
        )

    return country_a, country_b

def execute_query(
    question: str,
    country_a: str,
    country_b: str,
) -> dict[str, Any]:
    """
    Execute a natural-language analytical query
    against the canonical country-pair intelligence layer.
    """

    parsed = parse_query(
        question,
        country_a,
        country_b,
    )

    resolved_a, resolved_b = resolve_country_pair(
        parsed["country_a"],
        parsed["country_b"],
    )

    intent = QueryIntent(
        parsed["intent"]
    )

    con = get_connection()

    try:
        if intent == QueryIntent.RELATIONSHIP_PROFILE:
            result = relationship_profile(
                resolved_a,
                resolved_b,
                con=con,
            )

        elif intent == QueryIntent.RELATIONSHIP_HISTORY:
            result = relationship_history(
                resolved_a,
                resolved_b,
            )

        elif intent == QueryIntent.RELATIONSHIP_CHANGES:
            result = relationship_changes(
                resolved_a,
                resolved_b,
            )

        elif intent == QueryIntent.SUBSTANTIVE_DISAGREEMENT:
            result = substantive_pair_intelligence(
                con,
                resolved_a,
                resolved_b,
            )

        elif intent == QueryIntent.RESOLUTION_NLP:
            result = pair_resolution_nlp(
                con,
                resolved_a,
                resolved_b,
            )
        elif intent == QueryIntent.SUBJECT_TREND:
            result = subject_trends(
                con,
                resolved_a,
                resolved_b,
            )

        elif intent == QueryIntent.SUBJECT_RANKING:
            result = subject_rankings(
                con,
                resolved_a,
                resolved_b,
                order_by="disagreement",
            )

        elif intent == QueryIntent.ISSUE_POSITION:
            result = {
                resolved_a: issue_position_summary(
                    con,
                    resolved_a,
                ),
                resolved_b: issue_position_summary(
                    con,
                    resolved_b,
                ),
            }
        else:
            raise NotImplementedError(
                f"Query intent not yet implemented: {intent.value}"
            )

    finally:
        con.close()

    # Build a more specific answer for change-point questions.
    if intent == QueryIntent.RELATIONSHIP_CHANGES:
        if isinstance(result, pd.DataFrame) and not result.empty:
            changes = result.copy()

            if "change_magnitude" in changes.columns:
                changes["abs_change_magnitude"] = (
                    pd.to_numeric(
                        changes["change_magnitude"],
                        errors="coerce",
                    ).abs()
                )

                changes = changes.sort_values(
                    "abs_change_magnitude",
                    ascending=False,
                )

            top_changes = changes.head(5)

            parts = []

            for _, row in top_changes.iterrows():
                year = row.get("change_year", "")
                magnitude = row.get("change_magnitude")
                effect = row.get("effect_size")
                confirmed = row.get("confirmed", False)

                text = f"{int(year)}"

                if pd.notna(magnitude):
                    text += f" (change magnitude {float(magnitude):.3f})"

                if pd.notna(effect):
                    text += f", effect size {float(effect):.3f}"

                if bool(confirmed):
                    text += ", confirmed"

                parts.append(text)

            answer = (
                f"{len(changes)} relationship change points were detected. "
                f"The largest observed changes were: "
                + "; ".join(parts)
                + "."
            )
        else:
            answer = "No relationship change points were detected."

    else:
        answer = generate_answer(
            intent.value,
            result,
        )

    return {
        "question": question.strip(),
        "intent": intent.value,
        "country_a": resolved_a,
        "country_b": resolved_b,
        "answer": answer,
        "result": result,
        "evidence_source": "UN_VOTING",
        "provenance": "UN_VOTES_ANALYZER",
    }

__all__ = [
    "execute_query",
    "resolve_country",
    "resolve_country_pair",
    "classify_query",
    "parse_query",
]