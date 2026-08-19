from __future__ import annotations

import pandas as pd
import numpy as np
from pathlib import Path


GROUND_TRUTH = Path(
    "data/validation/temporal_ground_truth.csv"
)

CHANGE_POINTS = Path(
    "temporal_alignment_change_points.csv"
)

EPISODES = Path(
    "temporal_alignment_change_episodes.csv"
)

OUTPUT = Path(
    "temporal_error_analysis.csv"
)


def load_data():
    gt = pd.read_csv(GROUND_TRUTH)
    cp = pd.read_csv(CHANGE_POINTS)
    episodes = pd.read_csv(EPISODES)

    return gt, cp, episodes


def clean_year(value):
    if pd.isna(value):
        return np.nan

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return np.nan


def normalize_columns(df):
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    return df


def find_matching_episode(event, episodes):
    """
    Strict temporal matching.

    A detected episode matches a ground-truth event only if:
      1. country pair matches
      2. episode interval overlaps event interval

    Each event receives at most one matching episode.
    """

    event_start = clean_year(event["event_start"])
    event_end = clean_year(event["event_end"])

    if pd.isna(event_start) or pd.isna(event_end):
        return None

    pair = episodes[
        (episodes["country_a"] == event["country_a"])
        &
        (episodes["country_b"] == event["country_b"])
    ].copy()

    if pair.empty:
        return None

    # Strict temporal overlap
    pair = pair[
        (pair["episode_start"] <= event_end)
        &
        (pair["episode_end"] >= event_start)
    ].copy()

    if pair.empty:
        return None

    # If multiple episodes overlap, choose
    # the one with maximum overlap.
    pair["overlap_start"] = pair[
        "episode_start"
    ].clip(lower=event_start)

    pair["overlap_end"] = pair[
        "episode_end"
    ].clip(upper=event_end)

    pair["overlap_years"] = (
        pair["overlap_end"]
        - pair["overlap_start"]
        + 1
    )

    return pair.sort_values(
        "overlap_years",
        ascending=False
    ).iloc[0]

def nearest_change_point(
    event,
    change_points,
):
    pair = change_points[
        (change_points["country_a"] == event["country_a"])
        &
        (change_points["country_b"] == event["country_b"])
    ].copy()

    if pair.empty:
        return None

    event_start = clean_year(event["event_start"])
    event_end = clean_year(event["event_end"])

    if pd.isna(event_start) or pd.isna(event_end):
        return None

    pair["distance"] = pair[
        "change_year"
    ].apply(
        lambda year: (
            0
            if event_start <= year <= event_end
            else min(
                abs(year - event_start),
                abs(year - event_end),
            )
        )
    )

    return pair.sort_values(
        "distance"
    ).iloc[0]


def classify_error(
    episode,
    change_point,
):
    if episode is not None:
        return "EPISODE_AVAILABLE"

    if change_point is not None:
        return "CHANGE_POINT_ONLY"

    return "NO_DETECTION"


def analyze_event(
    event,
    episodes,
    change_points,
):
    episode = find_matching_episode(
        event,
        episodes,
    )

    change_point = nearest_change_point(
        event,
        change_points,
    )

    result = {
        "country_a": event["country_a"],
        "country_b": event["country_b"],
        "event_start": event["event_start"],
        "event_end": event["event_end"],
        "event_name": event["event_name"],
        "event_type": event.get(
            "event_type",
            "",
        ),
        "voting_relevance": event.get(
            "voting_relevance",
            "",
        ),
        "detection_status":
            "MISSED",
        "error_class":
            classify_error(
                episode,
                change_point,
            ),
        "nearest_episode_start": np.nan,
        "nearest_episode_end": np.nan,
        "nearest_peak_year": np.nan,
        "episode_distance": np.nan,
        "episode_magnitude": np.nan,
        "episode_effect_size": np.nan,
        "episode_confidence": np.nan,
        "nearest_change_year": np.nan,
        "change_point_distance": np.nan,
        "change_point_magnitude": np.nan,
        "change_point_effect_size": np.nan,
        "change_point_confirmed": False,
        "change_point_confidence": np.nan,
    }

    if episode is not None:

        event_start = clean_year(
            event["event_start"]
        )

        event_end = clean_year(
            event["event_end"]
        )

        episode_start = clean_year(
            episode["episode_start"]
        )

        episode_end = clean_year(
            episode["episode_end"]
        )

        overlap_start = max(
            event_start,
            episode_start,
        )

        overlap_end = min(
            event_end,
            episode_end,
        )

        overlap_years = max(
            0,
            overlap_end - overlap_start + 1,
        )

        result[
            "nearest_episode_start"
        ] = episode_start

        result[
            "nearest_episode_end"
        ] = episode_end

        result[
            "nearest_peak_year"
        ] = episode[
            "peak_change_year"
        ]

        # This is now overlap duration,
        # not distance.
        result[
            "episode_distance"
        ] = -float(overlap_years)

        result[
            "episode_magnitude"
        ] = episode[
            "max_change_magnitude"
        ]

        result[
            "episode_effect_size"
        ] = episode[
            "max_effect_size"
        ]

        result[
            "episode_confidence"
        ] = episode[
            "max_confidence"
        ]

        result[
            "detection_status"
        ] = "DETECTED"
    if change_point is not None:
        result[
            "nearest_change_year"
        ] = change_point[
            "change_year"
        ]

        result[
            "change_point_distance"
        ] = change_point[
            "distance"
        ]

        result[
            "change_point_magnitude"
        ] = change_point[
            "change_magnitude"
        ]

        result[
            "change_point_effect_size"
        ] = change_point[
            "effect_size"
        ]

        result[
            "change_point_confirmed"
        ] = bool(
            change_point["confirmed"]
        )

        result[
            "change_point_confidence"
        ] = change_point[
            "confidence"
        ]

    return result


def print_summary(result):
    print()
    print("=" * 90)
    print("TEMPORAL ERROR ANALYSIS")
    print("=" * 90)

    print()

    total = len(result)

    detected = (
        result["detection_status"]
        == "DETECTED"
    ).sum()

    missed = total - detected

    print(f"Ground-truth events: {total}")
    print(f"Detected events:     {detected}")
    print(f"Missed events:       {missed}")

    if total:
        print(
            f"Recall:              "
            f"{detected / total:.3f}"
        )

    print()
    print("=" * 90)
    print("ERROR CLASSIFICATION")
    print("=" * 90)

    print(
        result[
            "error_class"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print("=" * 90)
    print("EVENT-LEVEL ERROR ANALYSIS")
    print("=" * 90)

    columns = [
        "country_a",
        "country_b",
        "event_start",
        "event_end",
        "event_name",
        "detection_status",
        "error_class",
        "nearest_episode_start",
        "nearest_episode_end",
        "nearest_change_year",
        "change_point_distance",
        "change_point_magnitude",
        "change_point_effect_size",
        "change_point_confirmed",
    ]

    print(
        result[
            columns
        ].to_string(
            index=False
        )
    )

    print()
    print("=" * 90)
    print("ERROR ANALYSIS BY COUNTRY PAIR")
    print("=" * 90)

    pair_summary = (
        result
        .groupby(
            [
                "country_a",
                "country_b",
            ]
        )
        .agg(
            ground_truth_events=(
                "event_name",
                "count",
            ),
            detected_events=(
                "detection_status",
                lambda x:
                    (x == "DETECTED").sum(),
            ),
            missed_events=(
                "detection_status",
                lambda x:
                    (x == "MISSED").sum(),
            ),
            mean_nearest_cp_distance=(
                "change_point_distance",
                "mean",
            ),
        )
        .reset_index()
    )

    pair_summary["recall"] = (
        pair_summary["detected_events"]
        / pair_summary[
            "ground_truth_events"
        ]
    )

    print(
        pair_summary.to_string(
            index=False
        )
    )

    print()
    print("=" * 90)
    print("CANDIDATE MISSES WITH NEARBY CHANGE POINTS")
    print("=" * 90)

    candidates = result[
        (result["detection_status"] == "MISSED")
        &
        (result["change_point_distance"].notna())
        &
        (result["change_point_distance"] <= 5)
    ].copy()

    if candidates.empty:
        print(
            "No missed events have a "
            "change point within 5 years."
        )
    else:
        print(
            candidates[
                [
                    "country_a",
                    "country_b",
                    "event_start",
                    "event_end",
                    "event_name",
                    "nearest_change_year",
                    "change_point_distance",
                    "change_point_magnitude",
                    "change_point_effect_size",
                    "change_point_confirmed",
                    "change_point_confidence",
                ]
            ].to_string(
                index=False
            )
        )


def main():

    gt, change_points, episodes = load_data()

    gt = normalize_columns(gt)
    change_points = normalize_columns(
        change_points
    )
    episodes = normalize_columns(
        episodes
    )

    required_gt = {
        "country_a",
        "country_b",
        "event_start",
        "event_end",
        "event_name",
    }

    missing = (
        required_gt
        - set(gt.columns)
    )

    if missing:
        raise ValueError(
            "Ground truth missing columns: "
            f"{sorted(missing)}"
        )

    required_cp = {
        "country_a",
        "country_b",
        "change_year",
        "change_magnitude",
        "effect_size",
        "confirmed",
        "confidence",
    }

    missing = (
        required_cp
        - set(change_points.columns)
    )

    if missing:
        raise ValueError(
            "Change-point data missing columns: "
            f"{sorted(missing)}"
        )

    required_ep = {
        "country_a",
        "country_b",
        "episode_start",
        "episode_end",
        "peak_change_year",
        "max_change_magnitude",
        "max_effect_size",
        "max_confidence",
    }

    missing = (
        required_ep
        - set(episodes.columns)
    )

    if missing:
        raise ValueError(
            "Episode data missing columns: "
            f"{sorted(missing)}"
        )

    results = []

    for _, event in gt.iterrows():

        results.append(
            analyze_event(
                event,
                episodes,
                change_points,
            )
        )

    result = pd.DataFrame(
        results
    )

    result.to_csv(
        OUTPUT,
        index=False,
    )

    print_summary(result)

    print()
    print(
        f"Saved error analysis to: "
        f"{OUTPUT}"
    )

    print()
    print("=" * 90)
    print(
        "TEMPORAL ERROR ANALYSIS COMPLETE"
    )
    print("=" * 90)


if __name__ == "__main__":
    main()