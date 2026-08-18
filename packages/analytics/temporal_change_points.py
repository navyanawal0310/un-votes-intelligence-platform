from __future__ import annotations

import pandas as pd

from packages.analytics.change_points import (
    detect_change_points,
)


def detect_temporal_alignment_changes(
    temporal_alignment: pd.DataFrame,
    before_window: int = 3,
    after_window: int = 3,
    magnitude_threshold: float = 0.10,
    effect_threshold: float = 0.80,
    persistence_window: int = 2,
) -> pd.DataFrame:

    if temporal_alignment.empty:
        return pd.DataFrame()

    df = temporal_alignment.copy()

    required = [
        "country_a",
        "country_b",
        "window_end",
        "mean_alignment",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required temporal alignment columns: "
            f"{missing}"
        )

    # ---------------------------------------------------------
    # Normalize temporal alignment into change-point schema
    # ---------------------------------------------------------

    df["country_code"] = (
        df["country_a"].astype(str)
        + "_"
        + df["country_b"].astype(str)
    )

    df["issue"] = "TEMPORAL_ALIGNMENT"

    df["year"] = pd.to_numeric(
        df["window_end"],
        errors="coerce",
    )

    df["position_score"] = pd.to_numeric(
        df["mean_alignment"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "year",
            "position_score",
        ]
    )

    df = df.sort_values("year")

    # ---------------------------------------------------------
    # Run the existing validated detector
    # ---------------------------------------------------------

    changes = detect_change_points(
        df,
        before_window=before_window,
        after_window=after_window,
        magnitude_threshold=magnitude_threshold,
        effect_threshold=effect_threshold,
        persistence_window=persistence_window,
    )

    if changes.empty:
        return changes

    # ---------------------------------------------------------
    # Restore temporal-analysis metadata
    # ---------------------------------------------------------

    changes = changes.copy()

    changes["country_a"] = (
        df["country_a"].iloc[0]
    )

    changes["country_b"] = (
        df["country_b"].iloc[0]
    )

    return changes