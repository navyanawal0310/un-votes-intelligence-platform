from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

GROUND_TRUTH_PATH = Path(
    "data/validation/temporal_ground_truth.csv"
)

EPISODES_PATH = Path(
    "temporal_alignment_change_episodes.csv"
)

CHANGE_POINTS_PATH = Path(
    "temporal_alignment_change_points.csv"
)

OUTPUT_PATH = Path(
    "temporal_ground_truth_validation.csv"
)

# Maximum allowed distance between a ground-truth event
# and a detected episode when they do not directly overlap.
#
# Example:
# GT event = 2000
# detected = 2001
# difference = 1 year -> still match.
TEMPORAL_TOLERANCE = 2


VALID_DIRECTIONS = {-1, 0, 1}


# ============================================================
# HELPERS
# ============================================================

def normalize_country_pair(
    country_a: str,
    country_b: str,
) -> tuple[str, str]:

    return (
        str(country_a).strip().upper(),
        str(country_b).strip().upper(),
    )


def normalize_direction(value) -> int:

    if pd.isna(value):
        return 0

    if isinstance(value, str):

        value = value.strip().lower()

        if value in {
            "positive",
            "increase",
            "increasing",
            "up",
            "+1",
            "1",
        }:
            return 1

        if value in {
            "negative",
            "decrease",
            "decreasing",
            "down",
            "-1",
        }:
            return -1

        if value in {
            "neutral",
            "none",
            "unknown",
            "0",
        }:
            return 0

    try:
        value = float(value)

        if value > 0:
            return 1

        if value < 0:
            return -1

        return 0

    except (TypeError, ValueError):

        return 0


def safe_float(value) -> float:

    try:
        value = float(value)

        if np.isfinite(value):
            return value

    except (TypeError, ValueError):
        pass

    return 0.0


def overlap_length(
    start_a: int,
    end_a: int,
    start_b: int,
    end_b: int,
) -> int:

    start = max(start_a, start_b)
    end = min(end_a, end_b)

    if end < start:
        return 0

    return end - start + 1


def temporal_distance(
    start_a: int,
    end_a: int,
    start_b: int,
    end_b: int,
) -> int:

    overlap = overlap_length(
        start_a,
        end_a,
        start_b,
        end_b,
    )

    if overlap > 0:
        return 0

    if end_a < start_b:
        return start_b - end_a

    if end_b < start_a:
        return start_a - end_b

    return 0


def calculate_precision(
    tp: int,
    fp: int,
) -> float:

    denominator = tp + fp

    if denominator == 0:
        return 0.0

    return tp / denominator


def calculate_recall(
    tp: int,
    fn: int,
) -> float:

    denominator = tp + fn

    if denominator == 0:
        return 0.0

    return tp / denominator


def calculate_f1(
    precision: float,
    recall: float,
) -> float:

    denominator = precision + recall

    if denominator == 0:
        return 0.0

    return (
        2
        * precision
        * recall
        / denominator
    )


# ============================================================
# LOAD GROUND TRUTH
# ============================================================

def load_ground_truth() -> pd.DataFrame:

    if not GROUND_TRUTH_PATH.exists():

        raise FileNotFoundError(
            f"Ground-truth file not found: "
            f"{GROUND_TRUTH_PATH}"
        )

    df = pd.read_csv(
        GROUND_TRUTH_PATH
    )

    required = [
        "country_a",
        "country_b",
        "event_start",
        "event_end",
        "event_name",
        "event_type",
        "expected_direction",
        "voting_relevance",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            "Ground truth is missing required "
            f"columns: {missing}"
        )

    # Remove completely blank rows.
    df = df.dropna(
        how="all"
    ).copy()

    # Normalize country codes.
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

    # Numeric years.
    df["event_start"] = pd.to_numeric(
        df["event_start"],
        errors="coerce",
    )

    df["event_end"] = pd.to_numeric(
        df["event_end"],
        errors="coerce",
    )

    # Direction.
    df["expected_direction"] = (
        df["expected_direction"]
        .apply(normalize_direction)
    )

    # Strings.
    df["event_name"] = (
        df["event_name"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["event_type"] = (
        df["event_type"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["voting_relevance"] = (
        df["voting_relevance"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # Reject missing dates.
    invalid = df[
        df["event_start"].isna()
        | df["event_end"].isna()
    ]

    if not invalid.empty:

        raise ValueError(
            "Ground truth contains events with "
            "missing event_start/event_end.\n\n"
            f"{invalid.to_string(index=False)}\n\n"
            "Populate the nine historical events "
            "before running validation."
        )

    df["event_start"] = (
        df["event_start"]
        .astype(int)
    )

    df["event_end"] = (
        df["event_end"]
        .astype(int)
    )

    # Ensure start <= end.
    invalid_range = df[
        df["event_start"]
        > df["event_end"]
    ]

    if not invalid_range.empty:

        raise ValueError(
            "Ground-truth events have "
            "event_start > event_end."
        )

    return df.reset_index(
        drop=True
    )


# ============================================================
# LOAD DETECTED EPISODES
# ============================================================

def load_detected_episodes() -> pd.DataFrame:

    if not EPISODES_PATH.exists():

        raise FileNotFoundError(
            f"Episode file not found: "
            f"{EPISODES_PATH}"
        )

    df = pd.read_csv(
        EPISODES_PATH
    )

    required = [
        "country_a",
        "country_b",
        "episode_start",
        "episode_end",
        "peak_change_year",
        "max_change_magnitude",
        "max_effect_size",
        "max_confidence",
        "detections",
        "confirmed_detections",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            "Episode file is missing required "
            f"columns: {missing}"
        )

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

    numeric_columns = [
        "episode_start",
        "episode_end",
        "peak_change_year",
        "max_change_magnitude",
        "max_effect_size",
        "max_confidence",
        "detections",
        "confirmed_detections",
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.dropna(
        subset=[
            "episode_start",
            "episode_end",
            "peak_change_year",
        ]
    ).copy()

    df["episode_start"] = (
        df["episode_start"]
        .astype(int)
    )

    df["episode_end"] = (
        df["episode_end"]
        .astype(int)
    )

    df["peak_change_year"] = (
        df["peak_change_year"]
        .astype(int)
    )

    return df.reset_index(
        drop=True
    )


# ============================================================
# LOAD CHANGE-POINT DIRECTIONS
# ============================================================

def load_change_point_directions() -> pd.DataFrame:

    if not CHANGE_POINTS_PATH.exists():

        print(
            "WARNING: Change-point file not found."
        )

        return pd.DataFrame()

    df = pd.read_csv(
        CHANGE_POINTS_PATH
    )

    required = [
        "country_a",
        "country_b",
        "change_year",
        "mean_before",
        "mean_after",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:

        print(
            "WARNING: Change-point file is missing "
            f"columns: {missing}"
        )

        return pd.DataFrame()

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

    for column in [
        "change_year",
        "mean_before",
        "mean_after",
    ]:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.dropna(
        subset=[
            "change_year",
            "mean_before",
            "mean_after",
        ]
    ).copy()

    df["change_year"] = (
        df["change_year"]
        .astype(int)
    )

    df["direction"] = (
        df["mean_after"]
        - df["mean_before"]
    ).apply(normalize_direction)

    return df


# ============================================================
# ASSIGN DIRECTION TO EPISODES
# ============================================================

def attach_episode_direction(
    episodes: pd.DataFrame,
    change_points: pd.DataFrame,
) -> pd.DataFrame:

    episodes = episodes.copy()

    episodes["detected_direction"] = 0

    if change_points.empty:

        return episodes

    for index, episode in episodes.iterrows():

        pair = (
            change_points["country_a"]
            == episode["country_a"]
        ) & (
            change_points["country_b"]
            == episode["country_b"]
        )

        # Also support reversed country pairs.
        reverse_pair = (
            change_points["country_a"]
            == episode["country_b"]
        ) & (
            change_points["country_b"]
            == episode["country_a"]
        )

        candidates = change_points[
            pair | reverse_pair
        ].copy()

        if candidates.empty:
            continue

        candidates["distance"] = (
            candidates["change_year"]
            - episode["peak_change_year"]
        ).abs()

        candidates = candidates.sort_values(
            "distance"
        )

        nearest = candidates.iloc[0]

        direction = int(
            nearest["direction"]
        )

        # Reverse the direction if the stored
        # country ordering is opposite.
        if (
            nearest["country_a"]
            == episode["country_b"]
            and nearest["country_b"]
            == episode["country_a"]
        ):
            direction *= -1

        episodes.loc[
            index,
            "detected_direction",
        ] = direction

    return episodes


# ============================================================
# MATCH GROUND TRUTH EVENTS TO DETECTIONS
# ============================================================

def match_events(
    ground_truth: pd.DataFrame,
    episodes: pd.DataFrame,
) -> pd.DataFrame:

    matches = []

    used_episode_indices = set()

    for gt_index, gt in ground_truth.iterrows():

        best_index: Optional[int] = None
        best_distance = None
        best_overlap = 0

        for episode_index, episode in episodes.iterrows():

            if episode_index in used_episode_indices:
                continue

            same_pair = (
                gt["country_a"]
                == episode["country_a"]
                and gt["country_b"]
                == episode["country_b"]
            )

            reverse_pair = (
                gt["country_a"]
                == episode["country_b"]
                and gt["country_b"]
                == episode["country_a"]
            )

            if not (
                same_pair
                or reverse_pair
            ):
                continue

            distance = temporal_distance(
                int(gt["event_start"]),
                int(gt["event_end"]),
                int(episode["episode_start"]),
                int(episode["episode_end"]),
            )

            if distance > TEMPORAL_TOLERANCE:
                continue

            overlap = overlap_length(
                int(gt["event_start"]),
                int(gt["event_end"]),
                int(episode["episode_start"]),
                int(episode["episode_end"]),
            )

            # Prefer:
            # 1. larger overlap
            # 2. smaller temporal distance
            if (
                best_index is None
                or overlap > best_overlap
                or (
                    overlap == best_overlap
                    and distance < best_distance
                )
            ):

                best_index = episode_index
                best_distance = distance
                best_overlap = overlap

        if best_index is None:

            matches.append(
                {
                    "ground_truth_index": gt_index,
                    "detected": False,
                    "episode_index": None,
                    "temporal_overlap": 0.0,
                    "temporal_lead_lag": np.nan,
                    "direction_agreement": np.nan,
                }
            )

            continue

        used_episode_indices.add(
            best_index
        )

        episode = episodes.loc[
            best_index
        ]

        gt_duration = (
            int(gt["event_end"])
            - int(gt["event_start"])
            + 1
        )

        episode_duration = (
            int(episode["episode_end"])
            - int(episode["episode_start"])
            + 1
        )

        denominator = max(
            gt_duration,
            episode_duration,
        )

        overlap_ratio = (
            best_overlap / denominator
            if denominator > 0
            else 0.0
        )

        lead_lag = (
            int(episode["peak_change_year"])
            - int(gt["event_start"])
        )

        expected_direction = int(
            gt["expected_direction"]
        )

        detected_direction = int(
            episode["detected_direction"]
        )

        if expected_direction == 0:

            directional_agreement = 1.0

        else:

            directional_agreement = float(
                expected_direction
                == detected_direction
            )

        matches.append(
            {
                "ground_truth_index": gt_index,
                "detected": True,
                "episode_index": best_index,
                "temporal_overlap": overlap_ratio,
                "temporal_lead_lag": lead_lag,
                "direction_agreement":
                    directional_agreement,
            }
        )

    return pd.DataFrame(
        matches
    )


# ============================================================
# VALIDATION
# ============================================================

def validate():

    print("=" * 90)
    print("TEMPORAL GROUND-TRUTH VALIDATION")
    print("=" * 90)

    ground_truth = load_ground_truth()

    episodes = load_detected_episodes()

    change_points = (
        load_change_point_directions()
    )

    episodes = attach_episode_direction(
        episodes,
        change_points,
    )

    print()
    print(
        f"Ground-truth events: "
        f"{len(ground_truth)}"
    )

    print(
        f"Detected episodes: "
        f"{len(episodes)}"
    )

    # --------------------------------------------------------
    # MATCH EVENTS
    # --------------------------------------------------------

    matches = match_events(
        ground_truth,
        episodes,
    )

    matched_count = int(
        matches["detected"].sum()
    )

    false_negatives = (
        len(ground_truth)
        - matched_count
    )

    false_positives = (
        len(episodes)
        - matched_count
    )

    true_positives = matched_count

    precision = calculate_precision(
        true_positives,
        false_positives,
    )

    recall = calculate_recall(
        true_positives,
        false_negatives,
    )

    f1 = calculate_f1(
        precision,
        recall,
    )

    # --------------------------------------------------------
    # TEMPORAL METRICS
    # --------------------------------------------------------

    matched = matches[
        matches["detected"]
    ].copy()

    if matched.empty:

        mean_overlap = 0.0
        median_overlap = 0.0
        max_overlap = 0.0

        mean_lead_lag = np.nan
        median_lead_lag = np.nan

        early_detections = 0
        contemporaneous = 0
        delayed_detections = 0

        directional_agreement = np.nan

    else:

        mean_overlap = (
            matched["temporal_overlap"]
            .mean()
        )

        median_overlap = (
            matched["temporal_overlap"]
            .median()
        )

        max_overlap = (
            matched["temporal_overlap"]
            .max()
        )

        mean_lead_lag = (
            matched["temporal_lead_lag"]
            .mean()
        )

        median_lead_lag = (
            matched["temporal_lead_lag"]
            .median()
        )

        early_detections = int(
            (
                matched["temporal_lead_lag"]
                < 0
            ).sum()
        )

        contemporaneous = int(
            (
                matched["temporal_lead_lag"]
                == 0
            ).sum()
        )

        delayed_detections = int(
            (
                matched["temporal_lead_lag"]
                > 0
            ).sum()
        )

        directional_agreement = (
            matched["direction_agreement"]
            .mean()
        )

    # --------------------------------------------------------
    # MAIN SUMMARY
    # --------------------------------------------------------

    print()
    print("-" * 90)
    print("OVERALL PERFORMANCE")
    print("-" * 90)

    print(
        f"Ground-truth events: {len(ground_truth)}"
    )

    print(
        f"Detected episodes: {len(episodes)}"
    )

    print(
        f"Matched events: {true_positives}"
    )

    print(
        f"False positives: {false_positives}"
    )

    print(
        f"False negatives: {false_negatives}"
    )

    print(
        f"Precision: {precision:.3f}"
    )

    print(
        f"Recall: {recall:.3f}"
    )

    print(
        f"F1: {f1:.3f}"
    )

    print()
    print("-" * 90)
    print("TEMPORAL PERFORMANCE")
    print("-" * 90)

    print(
        f"Mean temporal overlap: "
        f"{mean_overlap:.3f}"
    )

    print(
        f"Median temporal overlap: "
        f"{median_overlap:.3f}"
    )

    print(
        f"Maximum temporal overlap: "
        f"{max_overlap:.3f}"
    )

    print(
        f"Mean temporal lead/lag: "
        f"{mean_lead_lag:.3f} years"
        if not pd.isna(mean_lead_lag)
        else "Mean temporal lead/lag: N/A"
    )

    print(
        f"Median temporal lead/lag: "
        f"{median_lead_lag:.3f} years"
        if not pd.isna(median_lead_lag)
        else "Median temporal lead/lag: N/A"
    )

    print(
        f"Early detections: "
        f"{early_detections}"
    )

    print(
        f"Contemporaneous detections: "
        f"{contemporaneous}"
    )

    print(
        f"Delayed detections: "
        f"{delayed_detections}"
    )

    print(
        f"Directional agreement: "
        f"{directional_agreement:.3f}"
        if not pd.isna(directional_agreement)
        else "Directional agreement: N/A"
    )

    # --------------------------------------------------------
    # VALIDATION BY RELEVANCE
    # --------------------------------------------------------

    print()
    print("-" * 90)
    print("PERFORMANCE BY VOTING RELEVANCE")
    print("-" * 90)

    relevance_rows = []

    for relevance in [
        "high",
        "medium",
        "low",
    ]:

        subset = ground_truth[
            ground_truth[
                "voting_relevance"
            ] == relevance
        ]

        if subset.empty:
            continue

        matched_indices = set(
            matches[
                matches["detected"]
            ]["ground_truth_index"]
            .tolist()
        )

        tp = sum(
            index in matched_indices
            for index in subset.index
        )

        fn = (
            len(subset)
            - tp
        )

        # False positives are only calculated
        # globally, because one detection can only
        # belong to one GT event.
        subset_recall = calculate_recall(
            tp,
            fn,
        )

        subset_precision = (
            tp / len(subset)
            if len(subset) > 0
            else 0
        )

        subset_f1 = calculate_f1(
            subset_precision,
            subset_recall,
        )

        relevance_rows.append(
            {
                "voting_relevance": relevance,
                "ground_truth_events":
                    len(subset),
                "detected":
                    tp,
                "recall":
                    subset_recall,
                "f1":
                    subset_f1,
            }
        )

    relevance_df = pd.DataFrame(
        relevance_rows
    )

    if not relevance_df.empty:

        print(
            relevance_df
            .round(3)
            .to_string(index=False)
        )

    # --------------------------------------------------------
    # PERFORMANCE BY COUNTRY PAIR
    # --------------------------------------------------------

    print()
    print("-" * 90)
    print("GROUND-TRUTH RESULTS BY COUNTRY PAIR")
    print("-" * 90)

    pair_rows = []

    for (country_a, country_b), group in (
        ground_truth
        .groupby(
            [
                "country_a",
                "country_b",
            ]
        )
    ):

        indices = set(
            group.index
        )

        detected_for_pair = (
            matches[
                matches["ground_truth_index"]
                .isin(indices)
            ]
        )

        detected_count = int(
            detected_for_pair[
                "detected"
            ].sum()
        )

        pair_recall = calculate_recall(
            detected_count,
            len(group) - detected_count,
        )

        pair_overlaps = (
            detected_for_pair[
                detected_for_pair["detected"]
            ]["temporal_overlap"]
        )

        pair_rows.append(
            {
                "country_a":
                    country_a,
                "country_b":
                    country_b,
                "ground_truth_events":
                    len(group),
                "detected":
                    detected_count,
                "recall":
                    pair_recall,
                "mean_overlap":
                    (
                        pair_overlaps.mean()
                        if not pair_overlaps.empty
                        else 0.0
                    ),
            }
        )

    pair_df = pd.DataFrame(
        pair_rows
    )

    if not pair_df.empty:

        print(
            pair_df
            .round(3)
            .to_string(index=False)
        )

    # --------------------------------------------------------
    # EVENT-LEVEL RESULTS
    # --------------------------------------------------------

    print()
    print("-" * 90)
    print("EVENT-LEVEL RESULTS")
    print("-" * 90)

    event_rows = []

    for _, gt in ground_truth.iterrows():

        result = matches[
            matches[
                "ground_truth_index"
            ] == _
        ]

        # Because `_` above is the dataframe
        # index, use the explicit index instead.
        gt_index = gt.name

        result = matches[
            matches[
                "ground_truth_index"
            ] == gt_index
        ]

        if result.empty:
            continue

        result = result.iloc[0]

        event_rows.append(
            {
                "country_a":
                    gt["country_a"],
                "country_b":
                    gt["country_b"],
                "event_start":
                    gt["event_start"],
                "event_end":
                    gt["event_end"],
                "event_name":
                    gt["event_name"],
                "event_type":
                    gt["event_type"],
                "voting_relevance":
                    gt["voting_relevance"],
                "expected_direction":
                    gt["expected_direction"],
                "detected":
                    bool(result["detected"]),
                "temporal_overlap":
                    result["temporal_overlap"],
                "temporal_lead_lag":
                    result["temporal_lead_lag"],
                "direction_agreement":
                    result["direction_agreement"],
            }
        )

    event_df = pd.DataFrame(
        event_rows
    )

    if not event_df.empty:

        print(
            event_df
            .round(3)
            .to_string(index=False)
        )

    # --------------------------------------------------------
    # SAVE RESULTS
    # --------------------------------------------------------

    output_rows = []

    for _, row in event_df.iterrows():

        output_rows.append(
            row.to_dict()
        )

    validation_df = pd.DataFrame(
        output_rows
    )

    validation_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print()
    print("-" * 90)

    print(
        f"Saved validation results to: "
        f"{OUTPUT_PATH}"
    )

    print()
    print("=" * 90)
    print("TEMPORAL GROUND-TRUTH VALIDATION COMPLETE")
    print("=" * 90)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    validate()