"""
Explainable relationship intelligence.

Converts existing quantitative, temporal, substantive,
and NLP evidence into an interpretable explanation.

This module does not change the underlying relationship score.

It is source-agnostic and preserves clean integration
points for future geopolitical/current-affairs evidence.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from packages.warehouse.database import get_connection
from packages.analytics.relationship_intelligence import (
    relationship_profile,
    relationship_history,
    relationship_changes,
)



def _score_band(score: float | None) -> str:
    """Interpret the magnitude of an existing relationship score."""

    if score is None:
        return "UNKNOWN"

    if score >= 0.80:
        return "VERY_HIGH"

    if score >= 0.65:
        return "HIGH"

    if score >= 0.50:
        return "MODERATE"

    if score >= 0.35:
        return "LOW"

    return "VERY_LOW"


def _trend_label(
    history: pd.DataFrame,
) -> str:
    """Describe the historical direction without changing the score."""

    if history.empty or len(history) < 2:
        return "INSUFFICIENT_HISTORY"

    scores = history[
        "relationship_score"
    ].dropna()

    if len(scores) < 2:
        return "INSUFFICIENT_HISTORY"

    first = float(scores.iloc[0])
    last = float(scores.iloc[-1])

    delta = last - first

    if delta >= 0.10:
        return "IMPROVING"

    if delta <= -0.10:
        return "DETERIORATING"

    return "STABLE"


def _stability_label(
    history: pd.DataFrame,
) -> str:
    """Classify historical volatility."""

    if history.empty:
        return "UNKNOWN"

    scores = history[
        "relationship_score"
    ].dropna()

    if len(scores) < 2:
        return "INSUFFICIENT_HISTORY"

    volatility = float(
        scores.max() - scores.min()
    )

    if volatility <= 0.10:
        return "STABLE"

    if volatility <= 0.25:
        return "MODERATE_VARIATION"

    return "HIGH_VARIATION"


def _confidence_label(
    evidence_count: int,
    temporal_rows: int,
    substantive_available: bool,
    change_points: int,
) -> str:
    """
    Assess evidence coverage.

    This is an evidence-confidence label, not a probability
    that the relationship classification is objectively true.
    """

    components = 0

    if evidence_count > 0:
        components += 1

    if temporal_rows > 0:
        components += 1

    if substantive_available:
        components += 1

    if change_points > 0:
        components += 1

    if components >= 3:
        return "HIGH"

    if components >= 2:
        return "MEDIUM"

    if components >= 1:
        return "LOW"

    return "INSUFFICIENT"

def _evidence_quality(
    profile: dict[str, Any],
    changes: pd.DataFrame,
    substantive: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Summarize the breadth and depth of available evidence.

    This is an evidence-coverage assessment, not a statistical
    probability or confidence interval.
    """

    evidence = profile["evidence"]

    relationship_rows = int(
        profile["relationship_rows"]
    )

    evidence_count = int(
        profile["evidence_count"]
    )

    temporal_rows = int(
        evidence["temporal_alignment"]
    )

    issue_rows = int(
        evidence["issue_attribution"]
    )

    episode_rows = int(
        evidence["episode_attribution"]
    )

    substantive_available = (
        substantive is not None
    )

    components = {
        "relationship_history": relationship_rows > 0,
        "temporal_alignment": temporal_rows > 0,
        "substantive_analysis": substantive_available,
        "issue_attribution": issue_rows > 0,
        "episode_attribution": episode_rows > 0,
        "change_point_analysis": True,
    }

    available_components = sum(
        components.values()
    )

    return {
        "evidence_count": evidence_count,
        "relationship_rows": relationship_rows,
        "temporal_alignment_rows": temporal_rows,
        "issue_attribution_rows": issue_rows,
        "episode_attribution_rows": episode_rows,
        "change_points": int(len(changes)),
        "substantive_available": substantive_available,
        "available_components": available_components,
        "total_components": len(components),
        "component_coverage": round(
            available_components
            / len(components),
            3,
        ),
        "components": components,
        "evidence_source": profile[
            "evidence_source"
        ],
        "provenance": profile[
            "provenance"
        ],
    }

def explain_relationship(
    country_a: str,
    country_b: str,
) -> dict[str, Any]:

    con = get_connection()

    try:
        profile = relationship_profile(
            country_a,
            country_b,
            con=con,
        )
    finally:
        con.close()

    history = relationship_history(
        country_a,
        country_b,
    )

    changes = relationship_changes(
        country_a,
        country_b,
    )

    score = profile[
        "relationship_score"
    ]

    substantive = profile[
        "substantive_intelligence"
    ]

    evidence = profile[
        "evidence"
    ]

    direction = profile[
        "relationship_direction"
    ]

    score_band = _score_band(score)

    trend = _trend_label(history)

    stability = _stability_label(history)

    trajectory = _trajectory_summary(
        history
    )

    topic_attribution = _topic_attribution(
        substantive
    )

    confidence = _confidence_label(
        profile["evidence_count"],
        evidence["temporal_alignment"],
        substantive is not None,
        len(changes),
    )
    evidence_quality = _evidence_quality(
        profile,
        changes,
        substantive,
    )

    evidence_drivers = _build_evidence_drivers(
        profile,
        changes,
    )

    explanation = []

    if score is not None:
        explanation.append(
            f"The latest relationship score is "
            f"{score:.3f}, classified as {score_band}."
        )

    if direction:
        explanation.append(
            f"The observed relationship direction is "
            f"{direction}."
        )

    stability_text = stability.lower()

    if stability_text.endswith("_variation"):
        stability_text = stability_text.replace(
            "_variation",
            " variation",
        )

    explanation.append(
        f"The historical trajectory is "
        f"{trend.lower()} with "
        f"{stability_text}."
    )

    if evidence["temporal_alignment"] > 0:
        explanation.append(
            f"The assessment is supported by "
            f"{evidence['temporal_alignment']} temporal "
            f"alignment observations."
        )

    if len(changes) > 0:
        explanation.append(
            f"{len(changes)} relationship change point(s) "
            f"were detected."
        )
    else:
        explanation.append(
            "No detected relationship change points "
            "are currently associated with this pair."
        )

    if substantive is not None:
        summary = substantive.get(
            "evidence_summary",
            {},
        )

        disagreement_count = summary.get(
            "resolution_disagreements",
            0,
        )

        if disagreement_count:
            explanation.append(
                f"Substantive analysis identifies "
                f"{disagreement_count} resolution-level "
                f"disagreements."
            )
    if topic_attribution["available"]:
        top_subject = topic_attribution["top_subject"]

        explanation.append(
            f"The dominant substantive disagreement "
            f"area is {top_subject}."
        )

        for item in topic_attribution["subjects"][:3]:
            explanation.append(
                f"{item['subject']} shows "
                f"{item['different_votes']} differing votes "
                f"across "
                f"{item['substantive_voting_events']} "
                f"substantive voting events "
                f"({item['disagreement_percentage']:.2f}% disagreement)."
            )
    if trajectory["available"]:
        explanation.append(
            f"The observed relationship trajectory spans "
            f"{trajectory['first_year']} to "
            f"{trajectory['last_year']}, with the score "
            f"moving from "
            f"{trajectory['first_score']:.3f} to "
            f"{trajectory['last_score']:.3f}."
        )

        explanation.append(
            f"The net change across the observed period is "
            f"{trajectory['net_change']:+.3f}."
        )

        explanation.append(
            f"The lowest observed score was "
            f"{trajectory['minimum_score']:.3f} in "
            f"{trajectory['minimum_year']}, while the "
            f"highest was "
            f"{trajectory['maximum_score']:.3f} in "
            f"{trajectory['maximum_year']}."
        )
        explanation.append(
        f"The assessment draws on "
        f"{evidence_quality['available_components']} "
        f"of {evidence_quality['total_components']} "
        f"available evidence components."
)

    return {
        "schema_version": "1.0",

        "pair": {
            "country_a": country_a.upper(),
            "country_b": country_b.upper(),
            "pair_key": profile["pair_key"],
        },

        "assessment": {
            "relationship_direction": direction,
            "relationship_score": score,
            "score_band": score_band,
            "historical_trend": trend,
            "historical_stability": stability,
            "confidence": confidence,
            "evidence_quality": evidence_quality,
            "trajectory": trajectory,
            "topic_attribution": topic_attribution,
        },

        "explanation": explanation,

        "evidence": {
            "evidence_drivers": evidence_drivers,
            "relationship_rows": profile[
                "relationship_rows"
            ],
            "evidence_count": profile[
                "evidence_count"
            ],
            "temporal_alignment_rows": evidence[
                "temporal_alignment"
            ],
            "change_points": len(changes),
            "issue_attribution_rows": evidence[
                "issue_attribution"
            ],
            "episode_attribution_rows": evidence[
                "episode_attribution"
            ],
            "substantive_available": (
                substantive is not None
            ),
        },

        "provenance": {
            "evidence_source": profile[
                "evidence_source"
            ],
            "provenance": profile[
                "provenance"
            ],
        },

        # Reserved for future evidence sources.
        "external_evidence": [],

        "future_sources": {
            "current_affairs": None,
            "geopolitical_events": None,
            "speeches": None,
            "diplomatic_events": None,
        },
    }

def _build_evidence_drivers(
    profile: dict[str, Any],
    changes: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Build interpretable evidence drivers.

    These explain the relationship state but do not
    mathematically reconstruct or modify the score.
    """

    drivers = []

    alignment = profile.get("alignment")

    if alignment is not None:
        if alignment >= 0.80:
            interpretation = "Strong voting alignment."
        elif alignment >= 0.60:
            interpretation = "Moderate voting alignment."
        else:
            interpretation = "Limited voting alignment."

        drivers.append(
            {
                "factor": "ALIGNMENT",
                "value": alignment,
                "interpretation": interpretation,
                "evidence_source": profile[
                    "evidence_source"
                ],
            }
        )

    divergence = profile.get("divergence")

    if divergence is not None:
        if divergence <= 0.20:
            interpretation = "Low observed divergence."
        elif divergence <= 0.40:
            interpretation = "Moderate observed divergence."
        else:
            interpretation = "High observed divergence."

        drivers.append(
            {
                "factor": "DIVERGENCE",
                "value": divergence,
                "interpretation": interpretation,
                "evidence_source": profile[
                    "evidence_source"
                ],
            }
        )

    directional_agreement = profile.get(
        "directional_agreement"
    )

    if directional_agreement is not None:
        if directional_agreement >= 0.80:
            interpretation = (
                "Strong directional agreement."
            )
        elif directional_agreement >= 0.60:
            interpretation = (
                "Moderate directional agreement."
            )
        else:
            interpretation = (
                "Weak directional agreement."
            )

        drivers.append(
            {
                "factor": "DIRECTIONAL_AGREEMENT",
                "value": directional_agreement,
                "interpretation": interpretation,
                "evidence_source": profile[
                    "evidence_source"
                ],
            }
        )

    temporal_rows = profile[
        "evidence"
    ]["temporal_alignment"]

    drivers.append(
        {
            "factor": "TEMPORAL_EVIDENCE",
            "value": temporal_rows,
            "interpretation": (
                f"{temporal_rows} temporal alignment "
                "observations are available."
            ),
            "evidence_source": profile[
                "evidence_source"
            ],
        }
    )

    change_count = len(changes)

    drivers.append(
        {
            "factor": "CHANGE_POINTS",
            "value": change_count,
            "interpretation": (
                "No detected relationship changes."
                if change_count == 0
                else (
                    f"{change_count} relationship "
                    "change point(s) detected."
                )
            ),
            "evidence_source": profile[
                "evidence_source"
            ],
        }
    )

    substantive = profile[
        "substantive_intelligence"
    ]

    if substantive is not None:
        summary = substantive.get(
            "evidence_summary",
            {},
        )

        disagreement_count = summary.get(
            "resolution_disagreements",
            0,
        )

        drivers.append(
            {
                "factor": "SUBSTANTIVE_DISAGREEMENT",
                "value": disagreement_count,
                "interpretation": (
                    f"{disagreement_count} resolution-level "
                    "disagreements identified."
                ),
                "evidence_source": substantive.get(
                    "evidence_source"
                ),
            }
    
        )

    return drivers

def _trajectory_summary(
    history: pd.DataFrame,
) -> dict[str, Any]:
    """
    Summarize the historical relationship trajectory.

    This describes the observed trajectory and does not
    modify the underlying relationship score.
    """

    if history.empty:
        return {
            "available": False,
            "rows": 0,
            "first_year": None,
            "last_year": None,
            "first_score": None,
            "last_score": None,
            "net_change": None,
            "minimum_score": None,
            "minimum_year": None,
            "maximum_score": None,
            "maximum_year": None,
        }

    data = (
        history[
            ["year", "relationship_score"]
        ]
        .dropna(subset=["relationship_score"])
        .sort_values("year")
        .reset_index(drop=True)
    )

    if data.empty:
        return {
            "available": False,
            "rows": 0,
            "first_year": None,
            "last_year": None,
            "first_score": None,
            "last_score": None,
            "net_change": None,
            "minimum_score": None,
            "minimum_year": None,
            "maximum_score": None,
            "maximum_year": None,
        }

    first = data.iloc[0]
    last = data.iloc[-1]

    minimum = data.loc[
        data["relationship_score"].idxmin()
    ]

    maximum = data.loc[
        data["relationship_score"].idxmax()
    ]

    return {
        "available": True,
        "rows": int(len(data)),

        "first_year": int(first["year"]),
        "last_year": int(last["year"]),

        "first_score": float(
            first["relationship_score"]
        ),

        "last_score": float(
            last["relationship_score"]
        ),

        "net_change": float(
            last["relationship_score"]
            - first["relationship_score"]
        ),

        "minimum_score": float(
            minimum["relationship_score"]
        ),

        "minimum_year": int(
            minimum["year"]
        ),

        "maximum_score": float(
            maximum["relationship_score"]
        ),

        "maximum_year": int(
            maximum["year"]
        ),
    }

def _topic_summary(
    substantive: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Extract and normalize substantive NLP themes.

    Themes are descriptive evidence and are not treated
    as causal explanations of the relationship score.
    """

    if not substantive:
        return {
            "available": False,
            "themes": [],
            "theme_count": 0,
        }

    themes = substantive.get(
        "themes",
    )

    if themes is None:
        summary = substantive.get(
            "evidence_summary",
            {},
        )

        themes = summary.get(
            "themes",
            {},
        )

    if not themes:
        return {
            "available": False,
            "themes": [],
            "theme_count": 0,
        }

    if isinstance(themes, dict):
        ranked = sorted(
            themes.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        normalized = [
            {
                "theme": str(theme),
                "count": int(count),
            }
            for theme, count in ranked
        ]

    elif isinstance(themes, list):
        normalized = themes

    else:
        normalized = []

    return {
        "available": bool(normalized),
        "themes": normalized,
        "theme_count": len(normalized),
    }

def _topic_attribution(
    substantive: dict[str, Any] | None,
    top_n: int = 10,
) -> dict[str, Any]:
    """
    Extract the dominant substantive disagreement subjects.

    This is descriptive evidence, not causal inference.
    """

    if not substantive:
        return {
            "available": False,
            "subjects": [],
            "top_subject": None,
        }

    rankings = substantive.get("subject_rankings")

    if rankings is None or rankings.empty:
        return {
            "available": False,
            "subjects": [],
            "top_subject": None,
        }

    required = {
        "subject",
        "substantive_voting_events",
        "matching_votes",
        "different_votes",
        "agreement_percentage",
        "disagreement_percentage",
    }

    missing = required - set(rankings.columns)

    if missing:
        raise ValueError(
            "Missing subject ranking columns: "
            f"{sorted(missing)}"
        )

    ranked = (
        rankings[
            [
                "subject",
                "substantive_voting_events",
                "matching_votes",
                "different_votes",
                "agreement_percentage",
                "disagreement_percentage",
            ]
        ]
        .copy()
        .sort_values(
            [
                "different_votes",
                "disagreement_percentage",
            ],
            ascending=False,
        )
        .head(top_n)
    )

    subjects = []

    for _, row in ranked.iterrows():
        subjects.append(
            {
                "subject": str(row["subject"]),
                "substantive_voting_events": int(
                    row["substantive_voting_events"]
                ),
                "matching_votes": int(
                    row["matching_votes"]
                ),
                "different_votes": int(
                    row["different_votes"]
                ),
                "agreement_percentage": float(
                    row["agreement_percentage"]
                ),
                "disagreement_percentage": float(
                    row["disagreement_percentage"]
                ),
            }
        )

    return {
        "available": bool(subjects),
        "subjects": subjects,
        "top_subject": (
            subjects[0]["subject"]
            if subjects
            else None
        ),
    }

__all__ = [
    "explain_relationship",
]