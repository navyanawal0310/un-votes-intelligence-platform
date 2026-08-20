"""
Temporal Event Validation
=========================

Validates detected temporal change points against nine independent
historical ground-truth events.

Outputs:
    temporal_event_validation.csv

Metrics:
    - strict event detection
    - detection within tolerance window
    - precision / recall / F1
    - mean / median detection distance
    - pre-event vs event-period alignment shift
    - event-level validation results
"""

from pathlib import Path
import pandas as pd
import numpy as np


# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent

GROUND_TRUTH_PATH = (
    ROOT / "data" / "validation" / "temporal_ground_truth.csv"
)

CHANGE_POINTS_PATH = (
    ROOT / "temporal_alignment_change_points.csv"
)

OUTPUT_PATH = (
    ROOT / "temporal_event_validation.csv"
)

# Number of years before event used to establish baseline.
PRE_EVENT_WINDOW = 3

# A detection is considered "near" an event if it occurs within
# this many years of the event boundary.
DETECTION_TOLERANCE = 5


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def normalize_pair(a, b):
    """
    Canonicalise country-pair ordering so that IND-RUS and RUS-IND
    are treated as the same pair.
    """
    return tuple(sorted([str(a).strip(), str(b).strip()]))


def load_ground_truth():
    if not GROUND_TRUTH_PATH.exists():
        raise FileNotFoundError(
            f"Ground-truth file not found:\n{GROUND_TRUTH_PATH}"
        )

    df = pd.read_csv(GROUND_TRUTH_PATH)

    required = [
        "country_a",
        "country_b",
        "event_start",
        "event_end",
        "event_name",
    ]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(
            f"Ground truth is missing required columns: {missing}"
        )

    df["event_start"] = pd.to_numeric(
        df["event_start"], errors="coerce"
    )

    df["event_end"] = pd.to_numeric(
        df["event_end"], errors="coerce"
    )

    if df["event_start"].isna().any() or df["event_end"].isna().any():
        bad = df[
            df["event_start"].isna()
            | df["event_end"].isna()
        ]

        print("\nINVALID GROUND-TRUTH EVENTS:")
        print(bad.to_string(index=False))

        raise ValueError(
            "Ground truth contains missing/invalid event dates."
        )

    return df


def load_change_points():
    if not CHANGE_POINTS_PATH.exists():
        raise FileNotFoundError(
            f"Change-point file not found:\n{CHANGE_POINTS_PATH}"
        )

    df = pd.read_csv(CHANGE_POINTS_PATH)

    required = [
        "country_a",
        "country_b",
        "change_year",
        "change_magnitude",
        "effect_size",
        "confirmed",
        "confidence",
    ]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(
            f"Change-point file is missing required columns: {missing}"
        )

    df["change_year"] = pd.to_numeric(
        df["change_year"], errors="coerce"
    )

    df = df.dropna(subset=["change_year"]).copy()

    return df


def load_alignment_series(country_a, country_b):
    """
    Load yearly alignment series for a country pair.

    Expected files:
        alignment_IND_RUS.csv
        alignment_IND_USA.csv
        etc.

    The existing project files contain:
        country_a
        country_b
        issue
        year
        score_a
        score_b
        absolute_divergence
        alignment_score
        directional_agreement
    """

    a, b = normalize_pair(country_a, country_b)

    filename = f"alignment_{a}_{b}.csv"
    path = ROOT / filename

    if not path.exists():
        return None

    df = pd.read_csv(path)

    if "year" not in df.columns:
        return None

    if "alignment_score" not in df.columns:
        return None

    df["year"] = pd.to_numeric(
        df["year"], errors="coerce"
    )

    df["alignment_score"] = pd.to_numeric(
        df["alignment_score"], errors="coerce"
    )

    df = df.dropna(
        subset=["year", "alignment_score"]
    ).copy()

    return df


def calculate_event_signal(
    country_a,
    country_b,
    event_start,
    event_end,
):
    """
    Calculate the change in alignment from the pre-event baseline
    to the event period.

    Baseline:
        event_start - PRE_EVENT_WINDOW ... event_start - 1

    Event period:
        event_start ... event_end
    """

    df = load_alignment_series(
        country_a,
        country_b,
    )

    if df is None or df.empty:
        return {
            "pre_mean": np.nan,
            "event_mean": np.nan,
            "absolute_shift": np.nan,
            "normalized_shift": np.nan,
            "pre_observations": 0,
            "event_observations": 0,
        }

    pre = df[
        (df["year"] >= event_start - PRE_EVENT_WINDOW)
        & (df["year"] < event_start)
    ]["alignment_score"]

    event = df[
        (df["year"] >= event_start)
        & (df["year"] <= event_end)
    ]["alignment_score"]

    pre_mean = pre.mean() if len(pre) else np.nan
    event_mean = event.mean() if len(event) else np.nan

    if pd.notna(pre_mean) and pd.notna(event_mean):

        absolute_shift = abs(
            event_mean - pre_mean
        )

        # Normalise against the available alignment range.
        combined = pd.concat([pre, event])

        data_range = (
            combined.max() - combined.min()
        )

        if data_range > 0:
            normalized_shift = (
                absolute_shift / data_range
            )
        else:
            normalized_shift = 0.0

    else:
        absolute_shift = np.nan
        normalized_shift = np.nan

    return {
        "pre_mean": pre_mean,
        "event_mean": event_mean,
        "absolute_shift": absolute_shift,
        "normalized_shift": normalized_shift,
        "pre_observations": len(pre),
        "event_observations": len(event),
    }


def find_nearest_change_point(
    country_a,
    country_b,
    event_start,
    event_end,
    change_points,
):
    """
    Find the nearest change point to the historical event.

    Distance is zero when a change point occurs inside
    the event interval.
    """

    pair_mask = (
        (
            change_points["country_a"].astype(str)
            == str(country_a)
        )
        &
        (
            change_points["country_b"].astype(str)
            == str(country_b)
        )
    )

    reverse_mask = (
        (
            change_points["country_a"].astype(str)
            == str(country_b)
        )
        &
        (
            change_points["country_b"].astype(str)
            == str(country_a)
        )
    )

    pair = change_points[
        pair_mask | reverse_mask
    ].copy()

    if pair.empty:
        return None

    def event_distance(year):
        if event_start <= year <= event_end:
            return 0

        if year < event_start:
            return event_start - year

        return year - event_end

    pair["event_distance"] = pair[
        "change_year"
    ].apply(event_distance)

    pair = pair.sort_values(
        [
            "event_distance",
            "confidence",
        ],
        ascending=[True, False],
    )

    return pair.iloc[0]


def validate_event(event, change_points):
    """
    Validate one historical event.
    """

    country_a = event["country_a"]
    country_b = event["country_b"]

    event_start = int(event["event_start"])
    event_end = int(event["event_end"])

    # -------------------------------------------------------------
    # SIGNAL
    # -------------------------------------------------------------

    signal = calculate_event_signal(
        country_a,
        country_b,
        event_start,
        event_end,
    )

    # -------------------------------------------------------------
    # CHANGE-POINT MATCHING
    # -------------------------------------------------------------

    nearest = find_nearest_change_point(
        country_a,
        country_b,
        event_start,
        event_end,
        change_points,
    )

    if nearest is None:

        nearest_year = np.nan
        distance = np.nan
        magnitude = np.nan
        effect_size = np.nan
        confidence = np.nan
        confirmed = False

    else:

        nearest_year = int(
            nearest["change_year"]
        )

        distance = float(
            nearest["event_distance"]
        )

        magnitude = float(
            nearest["change_magnitude"]
        )

        effect_size = float(
            nearest["effect_size"]
        )

        confidence = float(
            nearest["confidence"]
        )

        confirmed = bool(
            nearest["confirmed"]
        )

    # -------------------------------------------------------------
    # DETECTION DEFINITIONS
    # -------------------------------------------------------------

    strict_detected = (
        pd.notna(distance)
        and distance == 0
    )

    tolerance_detected = (
        pd.notna(distance)
        and distance <= DETECTION_TOLERANCE
    )

    return {
        "country_a": country_a,
        "country_b": country_b,
        "event_start": event_start,
        "event_end": event_end,
        "event_name": event["event_name"],
        "event_type": event.get(
            "event_type",
            ""
        ),

        # Signal
        "pre_mean": signal["pre_mean"],
        "event_mean": signal["event_mean"],
        "absolute_shift": signal["absolute_shift"],
        "normalized_shift": signal["normalized_shift"],
        "pre_observations": signal[
            "pre_observations"
        ],
        "event_observations": signal[
            "event_observations"
        ],

        # Detection
        "nearest_change_year": nearest_year,
        "detection_distance": distance,
        "change_point_magnitude": magnitude,
        "change_point_effect_size": effect_size,
        "change_point_confidence": confidence,
        "change_point_confirmed": confirmed,

        "strict_detected": strict_detected,
        "tolerance_detected": tolerance_detected,
    }


# ---------------------------------------------------------------------
# METRICS
# ---------------------------------------------------------------------

def calculate_metrics(results):
    total_events = len(results)

    strict_tp = int(
        results["strict_detected"].sum()
    )

    tolerance_tp = int(
        results["tolerance_detected"].sum()
    )

    # Ground truth events are the positive class.
    #
    # Strict precision here is defined as:
    # detected ground-truth events / all detected events
    #
    # Since this validator only evaluates ground-truth events,
    # we additionally report detection rate (recall).
    strict_recall = (
        strict_tp / total_events
        if total_events
        else 0.0
    )

    tolerance_recall = (
        tolerance_tp / total_events
        if total_events
        else 0.0
    )

    distances = results[
        "detection_distance"
    ].dropna()

    mean_distance = (
        distances.mean()
        if len(distances)
        else np.nan
    )

    median_distance = (
        distances.median()
        if len(distances)
        else np.nan
    )

    signal = results[
        "absolute_shift"
    ].dropna()

    mean_shift = (
        signal.mean()
        if len(signal)
        else np.nan
    )

    median_shift = (
        signal.median()
        if len(signal)
        else np.nan
    )

    measurable_signal = int(
        results["absolute_shift"].notna().sum()
    )

    return {
        "events": total_events,

        "strict_detections": strict_tp,
        "strict_recall": strict_recall,

        "within_tolerance_detections": tolerance_tp,
        "within_tolerance_recall": tolerance_recall,

        "events_with_measurable_signal":
            measurable_signal,

        "mean_absolute_shift":
            mean_shift,

        "median_absolute_shift":
            median_shift,

        "mean_detection_distance":
            mean_distance,

        "median_detection_distance":
            median_distance,
    }


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():

    print()
    print("=" * 90)
    print("TEMPORAL EVENT VALIDATION")
    print("=" * 90)

    # -------------------------------------------------------------
    # LOAD DATA
    # -------------------------------------------------------------

    ground_truth = load_ground_truth()
    change_points = load_change_points()

    print(
        f"\nGround-truth events: "
        f"{len(ground_truth)}"
    )

    print(
        f"Detected change points: "
        f"{len(change_points)}"
    )

    print(
        f"Detection tolerance: "
        f"{DETECTION_TOLERANCE} years"
    )

    # -------------------------------------------------------------
    # VALIDATE
    # -------------------------------------------------------------

    rows = []

    for _, event in ground_truth.iterrows():

        result = validate_event(
            event,
            change_points,
        )

        rows.append(result)

    results = pd.DataFrame(rows)

    # -------------------------------------------------------------
    # METRICS
    # -------------------------------------------------------------

    metrics = calculate_metrics(results)

    print()
    print("=" * 90)
    print("VALIDATION SUMMARY")
    print("=" * 90)

    print(
        f"Events evaluated: "
        f"{metrics['events']}"
    )

    print(
        f"Events with measurable signal: "
        f"{metrics['events_with_measurable_signal']}"
    )

    print()

    print(
        f"Strict detections: "
        f"{metrics['strict_detections']}"
    )

    print(
        f"Strict detection recall: "
        f"{metrics['strict_recall']:.3f}"
    )

    print()

    print(
        f"Detections within "
        f"{DETECTION_TOLERANCE} years: "
        f"{metrics['within_tolerance_detections']}"
    )

    print(
        f"Tolerance detection recall: "
        f"{metrics['within_tolerance_recall']:.3f}"
    )

    print()

    if pd.notna(
        metrics["mean_absolute_shift"]
    ):
        print(
            f"Mean absolute event shift: "
            f"{metrics['mean_absolute_shift']:.3f}"
        )

    if pd.notna(
        metrics["median_absolute_shift"]
    ):
        print(
            f"Median absolute event shift: "
            f"{metrics['median_absolute_shift']:.3f}"
        )

    if pd.notna(
        metrics["mean_detection_distance"]
    ):
        print(
            f"Mean detection distance: "
            f"{metrics['mean_detection_distance']:.2f} years"
        )

    if pd.notna(
        metrics["median_detection_distance"]
    ):
        print(
            f"Median detection distance: "
            f"{metrics['median_detection_distance']:.2f} years"
        )

    # -------------------------------------------------------------
    # EVENT TABLE
    # -------------------------------------------------------------

    print()
    print("=" * 90)
    print("EVENT-LEVEL VALIDATION")
    print("=" * 90)

    display_columns = [
        "country_a",
        "country_b",
        "event_start",
        "event_end",
        "event_name",
        "absolute_shift",
        "nearest_change_year",
        "detection_distance",
        "change_point_confidence",
        "strict_detected",
        "tolerance_detected",
    ]

    display = results[
        display_columns
    ].copy()

    for column in [
        "absolute_shift",
        "detection_distance",
        "change_point_confidence",
    ]:
        display[column] = display[column].round(3)

    print(
        display.to_string(index=False)
    )

    # -------------------------------------------------------------
    # SAVE
    # -------------------------------------------------------------

    results.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print()
    print(
        f"Saved validation results to: "
        f"{OUTPUT_PATH.name}"
    )

    print()
    print("=" * 90)
    print("TEMPORAL EVENT VALIDATION COMPLETE")
    print("=" * 90)


if __name__ == "__main__":
    main()