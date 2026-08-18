from __future__ import annotations

import pandas as pd


def build_change_episodes(
    changes: pd.DataFrame,
    max_gap: int = 2,
) -> pd.DataFrame:
    """
    Cluster nearby temporal change-point detections into
    higher-level change episodes.

    Detections belonging to the same country pair and separated
    by <= max_gap years are treated as one episode.
    """

    if changes.empty:
        return pd.DataFrame()

    required = [
        "country_a",
        "country_b",
        "change_year",
        "change_magnitude",
        "effect_size",
        "confirmed",
        "confidence",
    ]

    missing = [
        c for c in required
        if c not in changes.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    df = changes.copy()

    df["change_year"] = pd.to_numeric(
        df["change_year"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "country_a",
            "country_b",
            "change_year",
        ]
    )

    df["change_year"] = df["change_year"].astype(int)

    df = df.sort_values(
        [
            "country_a",
            "country_b",
            "change_year",
        ]
    )

    episodes = []

    for (country_a, country_b), group in df.groupby(
        ["country_a", "country_b"],
        sort=False,
    ):

        group = group.sort_values("change_year")

        current = []

        previous_year = None

        for _, row in group.iterrows():

            year = int(row["change_year"])

            if (
                previous_year is None
                or year - previous_year <= max_gap
            ):
                current.append(row)

            else:
                episodes.append(
                    _summarize_episode(
                        country_a,
                        country_b,
                        current,
                    )
                )

                current = [row]

            previous_year = year

        if current:
            episodes.append(
                _summarize_episode(
                    country_a,
                    country_b,
                    current,
                )
            )

    return pd.DataFrame(episodes)


def _summarize_episode(
    country_a,
    country_b,
    rows,
):

    group = pd.DataFrame(rows)

    peak_idx = group[
        "change_magnitude"
    ].abs().idxmax()

    peak = group.loc[peak_idx]

    return {
        "country_a": country_a,
        "country_b": country_b,

        "episode_start": int(
            group["change_year"].min()
        ),

        "episode_end": int(
            group["change_year"].max()
        ),

        "peak_change_year": int(
            peak["change_year"]
        ),

        "max_change_magnitude": float(
            group["change_magnitude"]
            .abs()
            .max()
        ),

        "max_effect_size": float(
            group["effect_size"]
            .abs()
            .max()
        ),

        "max_confidence": float(
            group["confidence"]
            .max()
        ),

        "detections": len(group),

        "confirmed_detections": int(
            group["confirmed"].sum()
        ),
    }