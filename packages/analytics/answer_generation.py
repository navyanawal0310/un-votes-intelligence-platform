"""
Natural-language answer generation for UN Votes Analyzer.

Converts structured analytical results into concise,
evidence-backed natural-language explanations.

This layer does not fetch external data and does not
perform independent analysis. It only interprets the
structured outputs produced by the analytical layer.
"""

from __future__ import annotations

from typing import Any
import pandas as pd

def _fmt_score(value: Any) -> str:
    if value is None:
        return "N/A"

    return f"{float(value):.3f}"


def generate_relationship_answer(
    result: dict[str, Any],
) -> str:
    """
    Generate a concise explanation from a relationship profile.
    """

    pair = result.get("pair", "UNKNOWN")
    score = result.get("relationship_score")
    direction = result.get(
        "relationship_direction",
        "UNKNOWN",
    )

    alignment = result.get("alignment")
    divergence = result.get("divergence")
    evidence_count = result.get(
        "evidence_count",
        0,
    )

    latest_year = result.get(
        "latest_year",
        "N/A",
    )

    lines = [
        f"{pair} relationship assessment",
        "",
        (
            f"Relationship direction: {direction}."
        ),
        (
            f"Relationship score: {_fmt_score(score)}."
        ),
    ]

    if alignment is not None:
        lines.append(
            f"Voting alignment: {_fmt_score(alignment)}."
        )

    if divergence is not None:
        lines.append(
            f"Observed divergence: {_fmt_score(divergence)}."
        )

    lines.append(
        f"Latest assessment year: {latest_year}."
    )

    lines.append(
        f"Evidence observations: {evidence_count}."
    )

    return "\n".join(lines)


def generate_substantive_answer(
    result: dict[str, Any],
) -> str:
    """
    Generate a concise natural-language explanation from
    substantive country-pair disagreement analysis.

    Handles both scalar disagreement counts and DataFrame
    resolution-level evidence.
    """

    pair = result.get(
        "pair",
        "UNKNOWN",
    )

    disagreement_data = result.get(
        "resolution_disagreements",
        0,
    )

    # resolution_disagreements may be a DataFrame.
    if isinstance(disagreement_data, pd.DataFrame):
        disagreements = len(disagreement_data)
    elif isinstance(disagreement_data, (list, tuple)):
        disagreements = len(disagreement_data)
    else:
        try:
            disagreements = int(disagreement_data)
        except (TypeError, ValueError):
            disagreements = 0

    lines = [
        f"{pair} substantive disagreement analysis",
        "",
        (
            f"Resolution-level disagreements: "
            f"{disagreements}."
        ),
    ]

    subject_rankings = result.get(
        "subject_rankings"
    )

    if isinstance(subject_rankings, pd.DataFrame):
        rows = subject_rankings.head(5).to_dict(
            orient="records"
        )

    elif isinstance(subject_rankings, list):
        rows = subject_rankings[:5]

    else:
        rows = []

    if rows:
        lines.append("")
        lines.append(
            "Top substantive disagreement areas:"
        )

        for row in rows:
            subject = row.get(
                "subject",
                "Unknown subject",
            )

            percentage = row.get(
                "disagreement_percentage"
            )

            if percentage is not None:
                lines.append(
                    f"- {subject}: "
                    f"{float(percentage):.2f}% disagreement"
                )

    evidence = result.get(
        "evidence_summary",
        {},
    )

    if isinstance(evidence, dict) and evidence:
        lines.append("")
        lines.append(
            "Evidence summary:"
        )

        for key, value in evidence.items():
            # Never print DataFrames directly.
            if isinstance(value, pd.DataFrame):
                value = len(value)

            lines.append(
                f"- {key}: {value}"
            )

    return "\n".join(lines)

def generate_history_answer(
    result: Any,
) -> str:
    """Summarize relationship history."""

    if not isinstance(result, pd.DataFrame):
        return "No relationship history is available."

    if result.empty:
        return "No relationship history is available."

    first = result.iloc[0]
    last = result.iloc[-1]

    first_year = int(first["year"])
    last_year = int(last["year"])

    first_score = float(
        first["relationship_score"]
    )
    last_score = float(
        last["relationship_score"]
    )

    net_change = last_score - first_score

    return (
        f"Relationship history spans "
        f"{first_year} to {last_year}. "
        f"The relationship score moved from "
        f"{first_score:.3f} to {last_score:.3f}, "
        f"a net change of {net_change:+.3f}."
    )


def generate_changes_answer(
    result: Any,
) -> str:
    """Summarize detected relationship changes."""

    if not isinstance(result, pd.DataFrame):
        return "No relationship change data is available."

    if result.empty:
        return "No relationship change points were detected."

    lines = [
        f"{len(result)} relationship change points were detected."
    ]

    if "change_year" in result.columns:
        years = (
            result["change_year"]
            .dropna()
            .astype(int)
            .tolist()
        )

        if years:
            lines.append(
                "Detected change years: "
                + ", ".join(map(str, years[:10]))
            )

    return "\n".join(lines)


def generate_subject_ranking_answer(
    result: Any,
) -> str:
    """Summarize subject-level disagreement rankings."""

    if isinstance(result, pd.DataFrame):
        rankings = result

    elif isinstance(result, dict):
        rankings = result.get("subject_rankings")

        if not isinstance(rankings, pd.DataFrame):
            if isinstance(rankings, list):
                rankings = pd.DataFrame(rankings)
            else:
                return "No subject ranking is available."

    else:
        return "No subject ranking is available."

    if rankings.empty:
        return "No subject ranking is available."

    lines = [
        "Top substantive disagreement areas:"
    ]

    for _, row in rankings.head(5).iterrows():

        subject = row.get(
            "subject",
            "Unknown subject",
        )

        percentage = row.get(
            "disagreement_percentage"
        )

        if pd.notna(percentage):
            lines.append(
                f"- {subject}: "
                f"{float(percentage):.2f}% disagreement"
            )
        else:
            lines.append(
                f"- {subject}"
            )

    return "\n".join(lines)

def generate_subject_trend_answer(
    result: Any,
) -> str:
    """Summarize subject-level trends."""

    if not isinstance(result, pd.DataFrame):
        return "No subject trend data is available."

    if result.empty:
        return "No subject trend data is available."

    lines = [
        f"Subject-level voting trends contain "
        f"{len(result)} observations."
    ]

    if "year" in result.columns:
        years = result["year"].dropna()

        if not years.empty:
            lines.append(
                f"Observed period: "
                f"{int(years.min())}–{int(years.max())}."
            )

    if "subject" in result.columns:
        subjects = (
            result["subject"]
            .dropna()
            .astype(str)
            .nunique()
        )

        lines.append(
            f"Subjects represented: {subjects}."
        )

    return "\n".join(lines)


def generate_issue_position_answer(
    result: Any,
) -> str:
    """Summarize country-level issue positions."""

    if not isinstance(result, dict):
        return "No issue-position analysis is available."

    lines = [
        "Issue-position analysis:"
    ]

    for country, data in result.items():
        if isinstance(data, pd.DataFrame):
            lines.append(
                f"- {country}: "
                f"{len(data)} issue-position records."
            )

        elif isinstance(data, dict):
            lines.append(
                f"- {country}: "
                f"{len(data)} issue categories."
            )

        else:
            lines.append(
                f"- {country}: analysis available."
            )

    return "\n".join(lines)


def generate_resolution_nlp_answer(
    result: Any,
) -> str:
    """Summarize resolution-level NLP analysis."""

    if not isinstance(result, dict):
        return "No resolution NLP analysis is available."

    disagreement_count = result.get(
        "disagreement_resolutions",
        0,
    )

    similarity = result.get(
        "similarity_to_agreement"
    )

    keywords = result.get(
        "keywords",
        [],
    )

    lines = [
        "Resolution-level NLP analysis:",
        (
            f"- Disagreement resolutions: "
            f"{disagreement_count}"
        ),
    ]

    if similarity is not None:
        lines.append(
            f"- Similarity to agreement corpus: "
            f"{float(similarity):.3f}"
        )

    if keywords:
        terms = [
            item.get("term")
            for item in keywords[:5]
            if item.get("term")
        ]

        if terms:
            lines.append(
                "- Dominant terms: "
                + ", ".join(terms)
            )

    return "\n".join(lines)
def generate_answer(
    intent: str,
    result: Any,
) -> str:
    """
    Convert a structured analytical result into
    a concise natural-language answer.
    """

    if intent == "RELATIONSHIP_PROFILE":
        return generate_relationship_answer(result)

    if intent == "RELATIONSHIP_HISTORY":
        return generate_history_answer(result)

    if intent == "RELATIONSHIP_CHANGES":
        return generate_changes_answer(result)

    if intent == "SUBSTANTIVE_DISAGREEMENT":
        return generate_substantive_answer(result)

    if intent == "RESOLUTION_NLP":
        return generate_resolution_nlp_answer(result)

    if intent == "SUBJECT_TREND":
        return generate_subject_trend_answer(result)

    if intent == "SUBJECT_RANKING":
        return generate_subject_ranking_answer(result)

    if intent == "ISSUE_POSITION":
        return generate_issue_position_answer(result)

    return (
        "The analytical result is available "
        "in structured form."
    )

__all__ = [
    "generate_answer",
    "generate_relationship_answer",
    "generate_substantive_answer",
]