"""
Substantive intelligence adapter.

Combines existing issue, subject and resolution analytics
into a source-agnostic country-pair evidence bundle.

This module does not fetch external/current-affairs data.
It provides a clean evidence boundary for future sources.
"""

from __future__ import annotations

from typing import Any

import duckdb
import pandas as pd

from packages.analytics.issue_positions import (
    issue_positions,
)
from packages.analytics.resolutions import (
    country_disagreements,
)
from packages.analytics.subject_rankings import (
    subject_rankings,
)
from packages.analytics.subject_trends import (
    subject_trends,
)


def substantive_pair_intelligence(
    con: duckdb.DuckDBPyConnection,
    country_a: str,
    country_b: str,
    *,
    min_subject_events: int = 5,
    min_trend_events: int = 10,
    min_issue_events: int = 3,
) -> dict[str, Any]:
    """
    Build substantive evidence for a country pair.

    The returned structure is deliberately source-agnostic so
    future geopolitical/current-affairs evidence can be attached
    without redesigning the UN-voting evidence model.
    """

    country_a = country_a.strip().upper()
    country_b = country_b.strip().upper()

    if country_a == country_b:
        raise ValueError(
            "country_a and country_b must be different."
        )

    rankings = subject_rankings(
        con,
        country_a,
        country_b,
        min_events=min_subject_events,
        order_by="disagreement",
    )

    trends = subject_trends(
        con,
        country_a,
        country_b,
        min_events=min_trend_events,
    )

    disagreements = country_disagreements(
        con,
        country_a,
        country_b,
    )

    positions_a = issue_positions(
        con,
        country_a,
        min_events=min_issue_events,
    )

    positions_b = issue_positions(
        con,
        country_b,
        min_events=min_issue_events,
    )

    return {
        "pair": f"{country_a}-{country_b}",
        "country_a": country_a,
        "country_b": country_b,

        "subject_rankings": rankings,
        "subject_trends": trends,

        "resolution_disagreements": disagreements,

        "issue_positions": {
            country_a: positions_a,
            country_b: positions_b,
        },

        "evidence_summary": {
            "subjects": int(
                rankings["subject"].nunique()
            )
            if not rankings.empty
            else 0,

            "subject_trend_rows": len(trends),

            "resolution_disagreements": len(
                disagreements
            ),

            "issue_rows_country_a": len(
                positions_a
            ),

            "issue_rows_country_b": len(
                positions_b
            ),
        },

        # Future evidence boundary.
        "external_evidence": [],

        "evidence_source": "UN_VOTING",

        "provenance": "UN_VOTES_ANALYZER",
    }