from __future__ import annotations

import pandas as pd

from packages.analytics.change_points import (
    detect_pair_change_points,
    consolidate_change_points,
)


def detect_temporal_alignment_changes(
    temporal_alignment: pd.DataFrame,
    before_window: int = 3,
    after_window: int = 3,
    magnitude_threshold: float = 0.10,
    effect_threshold: float = 0.80,
    persistence_window: int = 3,
) -> pd.DataFrame:

    if temporal_alignment.empty:
        return pd.DataFrame()

    required = {
        "country_a",
        "country_b",
        "window_end",
        "mean_alignment",
    }

    missing = sorted(
        required - set(temporal_alignment.columns)
    )

    if missing:
        raise ValueError(
            f"Missing required temporal alignment columns: {missing}"
        )

    df = temporal_alignment.copy()

    df["country_a"] = (
        df["country_a"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["country_b"] = (
        df["country_b"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["window_end"] = pd.to_numeric(
        df["window_end"],
        errors="coerce",
    )

    df["mean_alignment"] = pd.to_numeric(
        df["mean_alignment"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "country_a",
            "country_b",
            "window_end",
            "mean_alignment",
        ]
    ).copy()

    if df.empty:
        return pd.DataFrame()

    # ---------------------------------------------------------
    # Pair-level change-point detection
    # ---------------------------------------------------------

    changes = detect_pair_change_points(
        df,
        value_column="mean_alignment",
        year_column="window_end",
        country_a_column="country_a",
        country_b_column="country_b",
        before_window=before_window,
        after_window=after_window,
        magnitude_threshold=magnitude_threshold,
        effect_threshold=effect_threshold,
        persistence_window=persistence_window,
    )

    if changes.empty:
        return pd.DataFrame(
            columns=[
                "country_a",
                "country_b",
                "pair",
                "change_year",
                "mean_before",
                "mean_after",
                "change_magnitude",
                "effect_size",
                "persistence",
                "low_variance_shift",
                "confirmed",
                "confidence",
            ]
        )

    # ---------------------------------------------------------
    # Canonical pair key
    # ---------------------------------------------------------

    changes["country_a"] = (
        changes["country_a"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    changes["country_b"] = (
        changes["country_b"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    changes["pair"] = [
        "-".join(
            sorted(
                [
                    a,
                    b,
                ]
            )
        )
        for a, b in zip(
            changes["country_a"],
            changes["country_b"],
        )
    ]

    # ---------------------------------------------------------
    # Consolidate nearby detections
    # ---------------------------------------------------------

    changes["country_code"] = (
        changes["country_a"]
        + "_"
        + changes["country_b"]
    )

    changes["issue"] = "TEMPORAL_ALIGNMENT"

    changes = consolidate_change_points(
        changes,
        min_separation=3,
    )

    # Rebuild canonical pair after consolidation
    changes["pair"] = [
        "-".join(
            sorted(
                [
                    str(a).strip().upper(),
                    str(b).strip().upper(),
                ]
            )
        )
        for a, b in zip(
            changes["country_a"],
            changes["country_b"],
        )
    ]

    return changes[
        [
            "country_a",
            "country_b",
            "pair",
            "change_year",
            "mean_before",
            "mean_after",
            "change_magnitude",
            "effect_size",
            "persistence",
            "low_variance_shift",
            "confirmed",
            "confidence",
        ]
    ].sort_values(
        [
            "country_a",
            "country_b",
            "change_year",
        ]
    ).reset_index(drop=True)