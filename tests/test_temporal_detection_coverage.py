import os
import numpy as np
import pandas as pd


GROUND_TRUTH = "data/validation/temporal_ground_truth.csv"
ALIGNMENT = "country_pair_alignment.csv"
CHANGE_POINTS = "temporal_alignment_change_points.csv"

OUTPUT = "temporal_detection_coverage.csv"


PRE_YEARS = 3
POST_YEARS = 3
DETECTION_TOLERANCE = 5


def normalize_pair(a, b):
    return tuple(sorted([
        str(a).strip(),
        str(b).strip()
    ]))


def load_ground_truth():

    df = pd.read_csv(GROUND_TRUTH)

    required = [
        "country_a",
        "country_b",
        "event_start",
        "event_end",
        "event_name",
    ]

    missing = [
        c for c in required
        if c not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Ground truth missing columns: {missing}"
        )

    df = df.copy()

    df["event_start"] = pd.to_numeric(
        df["event_start"],
        errors="coerce"
    )

    df["event_end"] = pd.to_numeric(
        df["event_end"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["event_start", "event_end"]
    )

    df["pair"] = df.apply(
        lambda r: normalize_pair(
            r["country_a"],
            r["country_b"]
        ),
        axis=1
    )

    return df


def load_alignment():

    df = pd.read_csv(ALIGNMENT)

    required = [
        "country_a",
        "country_b",
        "year",
        "alignment_score",
    ]

    missing = [
        c for c in required
        if c not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Alignment file missing columns: {missing}"
        )

    df = df.copy()

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce"
    )

    df["alignment_score"] = pd.to_numeric(
        df["alignment_score"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["year", "alignment_score"]
    )

    df["pair"] = df.apply(
        lambda r: normalize_pair(
            r["country_a"],
            r["country_b"]
        ),
        axis=1
    )

    return df


def load_change_points():

    df = pd.read_csv(CHANGE_POINTS)

    required = [
        "country_a",
        "country_b",
        "change_year",
    ]

    missing = [
        c for c in required
        if c not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Change-point file missing columns: {missing}"
        )

    df = df.copy()

    df["change_year"] = pd.to_numeric(
        df["change_year"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["change_year"]
    )

    df["pair"] = df.apply(
        lambda r: normalize_pair(
            r["country_a"],
            r["country_b"]
        ),
        axis=1
    )

    return df


def nearest_change_point(
    pair,
    event_year,
    change_points
):

    candidates = change_points[
        change_points["pair"] == pair
    ]

    if candidates.empty:
        return np.nan, np.nan

    distances = (
        candidates["change_year"] - event_year
    ).abs()

    idx = distances.idxmin()

    year = candidates.loc[
        idx,
        "change_year"
    ]

    distance = abs(
        year - event_year
    )

    return year, distance


def calculate_event_coverage(
    event,
    alignment,
    change_points
):

    pair = event["pair"]

    event_start = int(
        event["event_start"]
    )

    event_end = int(
        event["event_end"]
    )

    # ---------------------------------------------------------
    # Alignment observations for this country pair
    # ---------------------------------------------------------

    pair_data = alignment[
        alignment["pair"] == pair
    ].copy()

    if pair_data.empty:
        return {
            "country_a": event["country_a"],
            "country_b": event["country_b"],
            "event_start": event_start,
            "event_end": event_end,
            "event_name": event["event_name"],
            "pre_observations": 0,
            "event_observations": 0,
            "post_observations": 0,
            "pre_mean": np.nan,
            "event_mean": np.nan,
            "post_mean": np.nan,
            "pre_event_shift": np.nan,
            "measurable_signal": False,
            "nearest_change_year": np.nan,
            "change_point_distance": np.nan,
            "detected_within_tolerance": False,
        }

    # ---------------------------------------------------------
    # Define windows
    # ---------------------------------------------------------

    pre_start = event_start - PRE_YEARS
    pre_end = event_start - 1

    post_start = event_end + 1
    post_end = event_end + POST_YEARS

    pre = pair_data[
        pair_data["year"].between(
            pre_start,
            pre_end
        )
    ]

    event_period = pair_data[
        pair_data["year"].between(
            event_start,
            event_end
        )
    ]

    post = pair_data[
        pair_data["year"].between(
            post_start,
            post_end
        )
    ]

    pre_mean = (
        pre["alignment_score"].mean()
        if not pre.empty
        else np.nan
    )

    event_mean = (
        event_period["alignment_score"].mean()
        if not event_period.empty
        else np.nan
    )

    post_mean = (
        post["alignment_score"].mean()
        if not post.empty
        else np.nan
    )

    # ---------------------------------------------------------
    # Event signal
    # ---------------------------------------------------------

    if pd.notna(pre_mean) and pd.notna(event_mean):

        pre_event_shift = abs(
            event_mean - pre_mean
        )

    else:

        pre_event_shift = np.nan

    measurable_signal = (
        pd.notna(pre_event_shift)
        and pre_event_shift >= 0.05
    )

    # ---------------------------------------------------------
    # Change-point detection
    # ---------------------------------------------------------

    nearest_year, distance = nearest_change_point(
        pair,
        event_start,
        change_points
    )

    detected_within_tolerance = (
        pd.notna(distance)
        and distance <= DETECTION_TOLERANCE
    )

    return {
        "country_a": event["country_a"],
        "country_b": event["country_b"],
        "event_start": event_start,
        "event_end": event_end,
        "event_name": event["event_name"],

        "pre_observations": len(pre),
        "event_observations": len(event_period),
        "post_observations": len(post),

        "pre_mean": pre_mean,
        "event_mean": event_mean,
        "post_mean": post_mean,

        "pre_event_shift": pre_event_shift,

        "measurable_signal": measurable_signal,

        "nearest_change_year": nearest_year,
        "change_point_distance": distance,

        "detected_within_tolerance":
            detected_within_tolerance,
    }


def main():

    print("=" * 80)
    print("TEMPORAL DETECTION COVERAGE")
    print("=" * 80)

    ground_truth = load_ground_truth()
    alignment = load_alignment()
    change_points = load_change_points()

    results = []

    for _, event in ground_truth.iterrows():

        result = calculate_event_coverage(
            event,
            alignment,
            change_points
        )

        results.append(result)

    result_df = pd.DataFrame(results)

    result_df.to_csv(
        OUTPUT,
        index=False
    )

    print()
    print("=" * 80)
    print("EVENT COVERAGE RESULTS")
    print("=" * 80)

    print(
        result_df[
            [
                "country_a",
                "country_b",
                "event_start",
                "event_name",
                "pre_event_shift",
                "measurable_signal",
                "nearest_change_year",
                "change_point_distance",
                "detected_within_tolerance",
            ]
        ].to_string(index=False)
    )

    total = len(result_df)

    measurable = int(
        result_df["measurable_signal"].sum()
    )

    detected = int(
        result_df["detected_within_tolerance"].sum()
    )

    measurable_and_detected = int(
        (
            result_df["measurable_signal"]
            & result_df["detected_within_tolerance"]
        ).sum()
    )

    print()
    print("=" * 80)
    print("COVERAGE SUMMARY")
    print("=" * 80)

    print(f"Ground-truth events: {total}")

    print(
        f"Events with measurable signal: "
        f"{measurable}"
    )

    print(
        f"Measurable-signal rate: "
        f"{measurable / total:.3f}"
        if total > 0
        else "Measurable-signal rate: 0.000"
    )

    print(
        f"Events detected within ±{DETECTION_TOLERANCE} years: "
        f"{detected}"
    )

    print(
        f"Overall detection coverage: "
        f"{detected / total:.3f}"
        if total > 0
        else "Overall detection coverage: 0.000"
    )

    if measurable > 0:

        print(
            f"Detection rate among measurable events: "
            f"{measurable_and_detected / measurable:.3f}"
        )

    print()
    print(
        f"Saved coverage analysis: {OUTPUT}"
    )

    print()
    print("=" * 80)
    print("TEMPORAL DETECTION COVERAGE COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()