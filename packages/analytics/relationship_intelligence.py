"""
Country-pair relationship intelligence layer.

This module provides a source-agnostic analytical interface
over the canonical UN voting evidence pipeline.

It does not fetch current affairs or geopolitical data.
It only creates clean integration points for future
evidence sources.
"""

from typing import Any

import duckdb
import pandas as pd

from analytical_pipeline import (
    get_pair_bundle,
    load_pipeline,
)

from packages.analytics.substantive_intelligence import (
    substantive_pair_intelligence,
)
from packages.warehouse.database import get_connection

def relationship_profile(
    country_a: str,
    country_b: str,
    pipeline: dict[str, pd.DataFrame] | None = None,
    con: duckdb.DuckDBPyConnection | None = None,
) -> dict[str, Any]:
    """
    Build an evidence-backed relationship profile
    for any country pair.
    """

    if pipeline is None:
        pipeline = load_pipeline()

    bundle = get_pair_bundle(
        pipeline,
        country_a,
        country_b,
    )

    relationship = bundle["relationship_state"].copy()

    if relationship.empty:
        raise ValueError(
            f"No relationship evidence available "
            f"for {country_a}-{country_b}"
        )

    latest = (
        relationship
        .sort_values("year")
        .iloc[-1]
    )
    owns_connection = False

    if con is None:
        con = get_connection()
        owns_connection = True

    try:
        substantive = substantive_pair_intelligence(
            con,
            country_a,
            country_b,
        )

    finally:
        if owns_connection:
            con.close()
    profile = {
        "pair": bundle["pair"],
        "pair_key": bundle["pair_key"],

        "latest_year": int(
            latest["year"]
        ),

        "relationship_direction": (
            latest["relationship_direction"]
        ),

        "relationship_score": (
            float(latest["relationship_score"])
            if pd.notna(latest["relationship_score"])
            else None
        ),

        "alignment": (
            float(latest["mean_alignment"])
            if pd.notna(latest["mean_alignment"])
            else None
        ),

        "divergence": (
            float(latest["mean_divergence"])
            if pd.notna(latest["mean_divergence"])
            else None
        ),

        "directional_agreement": (
            float(latest["directional_agreement"])
            if pd.notna(latest["directional_agreement"])
            else None
        ),

        "evidence_count": (
            int(latest["evidence_count"])
            if pd.notna(latest["evidence_count"])
            else 0
        ),

        "change_episode_count": int(
            len(bundle.get("change_episodes", pd.DataFrame()))
        ),

        "confirmed_episode_count": int(
            bundle["change_episodes"]["confirmed_detections"].sum()
            if (
                not bundle.get("change_episodes", pd.DataFrame()).empty
                and "confirmed_detections" in bundle["change_episodes"].columns
            )
            else 0
        ),

        "confirmed_episode_count": (
            int(relationship["confirmed_episode_count"].max())
            if "confirmed_episode_count" in relationship.columns
            else 0
        ),

        "evidence_source": (
            latest["evidence_source"]
            if pd.notna(latest["evidence_source"])
            else None
        ),

        "provenance": (
            latest["provenance"]
            if pd.notna(latest["provenance"])
            else None
        ),

        "change_points": len(
            bundle["change_points"]
        ),

        "change_episodes": (
            bundle["change_episodes"].to_dict(orient="records")
        ),

        "relationship_rows": len(
            relationship
        ),

        "evidence": {
            "temporal_alignment": len(
                bundle["temporal_alignment"]
            ),
            "change_points": len(
                bundle["change_points"]
            ),
            "issue_attribution": len(
                bundle["issue_attribution"]
            ),
            "episode_attribution": len(
                bundle["episode_attribution"]
            ),
        },

        # Future evidence integration point.
        "substantive_intelligence": substantive,

        # Future evidence integration point.
        "external_evidence": [],
       }

    return profile


def relationship_history(
    country_a: str,
    country_b: str,
    pipeline: dict[str, pd.DataFrame] | None = None,
) -> pd.DataFrame:
    """
    Return the complete historical relationship trajectory.
    """

    if pipeline is None:
        pipeline = load_pipeline()

    bundle = get_pair_bundle(
        pipeline,
        country_a,
        country_b,
    )

    return (
        bundle["relationship_state"]
        .sort_values("year")
        .reset_index(drop=True)
    )


def relationship_changes(
    country_a: str,
    country_b: str,
    pipeline: dict[str, pd.DataFrame] | None = None,
) -> pd.DataFrame:
    """
    Return detected relationship change points.
    """

    if pipeline is None:
        pipeline = load_pipeline()

    bundle = get_pair_bundle(
        pipeline,
        country_a,
        country_b,
    )

    return (
        bundle["change_points"]
        .sort_values("change_year")
        .reset_index(drop=True)
    )