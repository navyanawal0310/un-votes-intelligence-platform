"""
Structured country-pair intelligence report.

This layer converts analytical evidence into a stable,
API/UI-ready structure.

It intentionally does not implement current-affairs data.
The external_evidence field is reserved for future
geopolitical/current-affairs integration.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from packages.analytics.relationship_intelligence import (
    relationship_profile,
    relationship_history,
    relationship_changes,
)


def build_country_pair_report(
    country_a: str,
    country_b: str,
) -> dict[str, Any]:
    """
    Build a structured intelligence report for any
    country pair.
    """

    profile = relationship_profile(
        country_a,
        country_b,
    )

    history = relationship_history(
        country_a,
        country_b,
    )

    changes = relationship_changes(
        country_a,
        country_b,
    )
    substantive = profile[
        "substantive_intelligence"
    ]

    substantive_summary = (
        substantive["evidence_summary"]
        if substantive is not None
        else {
            "subjects": 0,
            "subject_trend_rows": 0,
            "resolution_disagreements": 0,
            "issue_rows_country_a": 0,
            "issue_rows_country_b": 0,
        }
    )

    report = {
        "schema_version": "1.0",

        "pair": {
            "country_a": country_a.upper(),
            "country_b": country_b.upper(),
            "pair_key": profile["pair_key"],
        },

        "current_state": {
            "year": profile["latest_year"],
            "direction": profile[
                "relationship_direction"
            ],
            "relationship_score": profile[
                "relationship_score"
            ],
            "alignment": profile["alignment"],
            "divergence": profile["divergence"],
            "directional_agreement": profile[
                "directional_agreement"
            ],
        },

                "evidence": {
            "evidence_count": profile[
                "evidence_count"
            ],
            "relationship_rows": profile[
                "relationship_rows"
            ],
            "temporal_alignment_rows": profile[
                "evidence"
            ]["temporal_alignment"],
            "change_points": len(changes),
            "issue_attribution_rows": profile[
                "evidence"
            ]["issue_attribution"],
            "episode_attribution_rows": profile[
                "evidence"
            ]["episode_attribution"],

            "substantive": {
                "subjects": substantive_summary[
                    "subjects"
                ],
                "subject_trend_rows": substantive_summary[
                    "subject_trend_rows"
                ],
                "resolution_disagreements": substantive_summary[
                    "resolution_disagreements"
                ],
                "issue_rows_country_a": substantive_summary[
                    "issue_rows_country_a"
                ],
                "issue_rows_country_b": substantive_summary[
                    "issue_rows_country_b"
                ],
            },
        },

        "history": {
            "years": (
                history["year"]
                .dropna()
                .astype(int)
                .tolist()
            ),
            "relationship_scores": (
                history["relationship_score"]
                .where(
                    pd.notna(
                        history["relationship_score"]
                    ),
                    None,
                )
                .tolist()
            ),
        },

        "change_points": (
            changes.to_dict(orient="records")
        ),
        
        "substantive_intelligence": {
            "available": substantive is not None,
            "evidence_source": (
                substantive["evidence_source"]
                if substantive is not None
                else None
            ),
            "provenance": (
                substantive["provenance"]
                if substantive is not None
                else None
            ),
            "summary": substantive_summary,
        },

        "provenance": {
            "evidence_source": profile[
                "evidence_source"
            ],
            "provenance": profile[
                "provenance"
            ],
        },

        # Reserved integration point for future:
        # geopolitical events, current affairs,
        # speeches, diplomatic developments, etc.
        "external_evidence": [],

        "future_sources": {
            "current_affairs": None,
            "geopolitical_events": None,
            "speeches": None,
            "diplomatic_events": None,
        },
    }

    return report