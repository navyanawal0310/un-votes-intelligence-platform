"""
UN Votes Analyzer
Temporal Robustness / Sensitivity Analysis

Purpose:
    Test whether temporal-event conclusions are stable under reasonable
    changes to:
        1. minimum signal threshold
        2. detection tolerance

This is NOT an optimization procedure.
We are looking for stability, not the highest possible score.
"""

from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

GROUND_TRUTH_FILE = (
    BASE_DIR
    / "data"
    / "validation"
    / "temporal_ground_truth.csv"
)

SIGNAL_FILE = (
    BASE_DIR
    / "temporal_event_conditioned_detection.csv"
)

OUTPUT_FILE = BASE_DIR / "temporal_robustness_analysis.csv"


# Reasonable signal thresholds.
# These should not be interpreted as optimized values.
SIGNAL_THRESHOLDS = [0.03, 0.05, 0.075, 0.10]

# Reasonable temporal detection tolerances.
TOLERANCES = [0, 1, 3, 5]


# ============================================================
# HELPERS
# ============================================================

def find_column(df, candidates, required=True):
    """
    Find the first available column from a list of alternatives.
    """

    for column in candidates:
        if column in df.columns:
            return column

    if required:
        raise ValueError(
            f"Required column not found.\n"
            f"Tried: {candidates}\n"
            f"Available columns: {list(df.columns)}"
        )

    return None


def normalize_pair(a, b):
    """
    Treat country pairs as unordered.

    IND-USA == USA-IND
    """

    return tuple(sorted([str(a), str(b)]))


def safe_divide(a, b):
    if b == 0:
        return 0.0
    return a / b


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("=" * 75)
    print("TEMPORAL ROBUSTNESS / SENSITIVITY ANALYSIS")
    print("=" * 75)

    if not GROUND_TRUTH_FILE.exists():
        raise FileNotFoundError(
            f"Missing ground truth file:\n{GROUND_TRUTH_FILE}"
        )

    if not SIGNAL_FILE.exists():
        raise FileNotFoundError(
            f"Missing signal file:\n{SIGNAL_FILE}"
        )

    ground_truth = pd.read_csv(GROUND_TRUTH_FILE)
    signal = pd.read_csv(SIGNAL_FILE)

    print()
    print(f"Ground-truth events loaded: {len(ground_truth)}")
    print(f"Signal observations loaded: {len(signal)}")

    return ground_truth, signal


# ============================================================
# PREPARE GROUND TRUTH
# ============================================================

def prepare_ground_truth(df):

    df = df.copy()

    pair_a = find_column(
        df,
        ["country_a"]
    )

    pair_b = find_column(
        df,
        ["country_b"]
    )

    event_start = find_column(
        df,
        ["event_start", "event_year", "start_year"]
    )

    event_end = find_column(
        df,
        ["event_end", "end_year"]
    )

    df["pair"] = [
        normalize_pair(a, b)
        for a, b in zip(df[pair_a], df[pair_b])
    ]

    df["event_start_year"] = pd.to_numeric(
        df[event_start],
        errors="coerce"
    )

    df["event_end_year"] = pd.to_numeric(
        df[event_end],
        errors="coerce"
    )

    # If event_end is missing, use event_start.
    df["event_end_year"] = df["event_end_year"].fillna(
        df["event_start_year"]
    )

    df = df.dropna(
        subset=["event_start_year"]
    ).copy()

    return df


# ============================================================
# PREPARE SIGNAL DATA
# ============================================================

def prepare_signal(df):

    df = df.copy()

    pair_a = find_column(
        df,
        ["country_a"]
    )

    pair_b = find_column(
        df,
        ["country_b"]
    )

    event_start = find_column(
        df,
        ["event_start", "event_year", "start_year"]
    )

    # Event-conditioned output normally has event_shift.
    signal_column = find_column(
        df,
        [
            "event_shift",
            "absolute_shift",
            "abs_event_shift",
            "change_magnitude"
        ]
    )

    df["pair"] = [
        normalize_pair(a, b)
        for a, b in zip(df[pair_a], df[pair_b])
    ]

    df["event_start_year"] = pd.to_numeric(
        df[event_start],
        errors="coerce"
    )

    df["signal_value"] = pd.to_numeric(
        df[signal_column],
        errors="coerce"
    ).abs()

    # Optional detected change-point information.
    cp_column = find_column(
        df,
        [
            "nearest_change_point_year",
            "change_year",
            "detected_year"
        ],
        required=False
    )

    if cp_column:
        df["detected_year"] = pd.to_numeric(
            df[cp_column],
            errors="coerce"
        )
    else:
        df["detected_year"] = np.nan

    return df


# ============================================================
# MATCH GROUND TRUTH TO SIGNAL
# ============================================================

def create_event_records(ground_truth, signal):

    records = []

    for _, gt in ground_truth.iterrows():

        pair = gt["pair"]
        event_start = gt["event_start_year"]
        event_end = gt["event_end_year"]

        candidates = signal[
            (signal["pair"] == pair) &
            (
                signal["event_start_year"]
                == event_start
            )
        ].copy()

        # If exact event-year matching fails, use the same
        # country pair and nearest event year.
        if candidates.empty:

            pair_candidates = signal[
                signal["pair"] == pair
            ].copy()

            if not pair_candidates.empty:

                pair_candidates["year_distance"] = (
                    pair_candidates["event_start_year"]
                    - event_start
                ).abs()

                nearest = pair_candidates.sort_values(
                    "year_distance"
                ).head(1)

                # Only accept a reasonably close event match.
                if (
                    not nearest.empty
                    and nearest.iloc[0]["year_distance"] <= 2
                ):
                    candidates = nearest

        if candidates.empty:

            records.append({
                "pair": pair,
                "event_start": event_start,
                "event_end": event_end,
                "signal": np.nan,
                "detected_year": np.nan
            })

            continue

        row = candidates.iloc[0]

        records.append({
            "pair": pair,
            "event_start": event_start,
            "event_end": event_end,
            "signal": row["signal_value"],
            "detected_year": row["detected_year"]
        })

    return pd.DataFrame(records)


# ============================================================
# EVALUATE ONE PARAMETER COMBINATION
# ============================================================

def evaluate_combination(
    events,
    signal_threshold,
    tolerance
):

    total_events = len(events)

    measurable = events[
        events["signal"].notna()
        & (events["signal"] >= signal_threshold)
    ].copy()

    measurable_count = len(measurable)

    detected_count = 0
    exact_count = 0
    errors = []

    for _, event in measurable.iterrows():

        detected_year = event["detected_year"]

        if pd.isna(detected_year):
            continue

        distance = abs(
            detected_year - event["event_start"]
        )

        errors.append(distance)

        if distance <= tolerance:
            detected_count += 1

        if distance == 0:
            exact_count += 1

    measurable_rate = safe_divide(
        measurable_count,
        total_events
    )

    detection_rate_all = safe_divide(
        detected_count,
        total_events
    )

    detection_rate_measurable = safe_divide(
        detected_count,
        measurable_count
    )

    exact_rate = safe_divide(
        exact_count,
        measurable_count
    )

    mean_error = (
        float(np.mean(errors))
        if errors
        else np.nan
    )

    median_error = (
        float(np.median(errors))
        if errors
        else np.nan
    )

    return {
        "signal_threshold": signal_threshold,
        "tolerance_years": tolerance,

        "ground_truth_events": total_events,

        "measurable_events": measurable_count,
        "measurable_rate": measurable_rate,

        "detected_events": detected_count,

        "detection_rate_all_events": detection_rate_all,
        "detection_rate_measurable": detection_rate_measurable,

        "exact_detections": exact_count,
        "exact_detection_rate": exact_rate,

        "mean_detection_error": mean_error,
        "median_detection_error": median_error
    }


# ============================================================
# RUN ROBUSTNESS MATRIX
# ============================================================

def run_analysis(events):

    results = []

    for threshold in SIGNAL_THRESHOLDS:

        for tolerance in TOLERANCES:

            result = evaluate_combination(
                events,
                threshold,
                tolerance
            )

            results.append(result)

    return pd.DataFrame(results)


# ============================================================
# DISPLAY
# ============================================================

def display_results(results):

    print()
    print("=" * 75)
    print("ROBUSTNESS MATRIX")
    print("=" * 75)

    display_columns = [
        "signal_threshold",
        "tolerance_years",
        "measurable_events",
        "measurable_rate",
        "detected_events",
        "detection_rate_all_events",
        "detection_rate_measurable",
        "mean_detection_error"
    ]

    display_df = results[display_columns].copy()

    for column in [
        "measurable_rate",
        "detection_rate_all_events",
        "detection_rate_measurable"
    ]:
        display_df[column] = display_df[column].round(3)

    display_df["mean_detection_error"] = (
        display_df["mean_detection_error"]
        .round(2)
    )

    print(
        display_df.to_string(index=False)
    )


# ============================================================
# STABILITY SUMMARY
# ============================================================

def calculate_stability(results):

    print()
    print("=" * 75)
    print("ROBUSTNESS SUMMARY")
    print("=" * 75)

    measurable_rates = results[
        "measurable_rate"
    ].dropna()

    detection_rates = results[
        "detection_rate_all_events"
    ].dropna()

    print(
        f"Measurable-event rate range: "
        f"{measurable_rates.min():.3f} - "
        f"{measurable_rates.max():.3f}"
    )

    print(
        f"Overall detection-rate range: "
        f"{detection_rates.min():.3f} - "
        f"{detection_rates.max():.3f}"
    )

    print()

    # Check whether the number of measurable events is
    # reasonably stable across thresholds.
    counts = results.groupby(
        "signal_threshold"
    )["measurable_events"].first()

    print("Measurable events by signal threshold:")

    for threshold, count in counts.items():

        print(
            f"  threshold {threshold:.3f}: "
            f"{int(count)} events"
        )

    print()

    # Identify the conservative operating region.
    stable = results[
        (results["signal_threshold"] >= 0.05)
        & (results["signal_threshold"] <= 0.10)
        & (results["tolerance_years"] <= 5)
    ]

    if not stable.empty:

        stable_detection = stable[
            "detection_rate_all_events"
        ]

        print(
            "Conservative operating-region "
            f"detection range: "
            f"{stable_detection.min():.3f} - "
            f"{stable_detection.max():.3f}"
        )

    print()
    print(
        "Interpretation:"
    )
    print(
        "This analysis evaluates robustness rather than "
        "optimizing parameters."
    )
    print(
        "A threshold should only be considered credible if "
        "the substantive conclusion remains reasonably "
        "stable across nearby values."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    ground_truth, signal = load_data()

    ground_truth = prepare_ground_truth(
        ground_truth
    )

    signal = prepare_signal(
        signal
    )

    events = create_event_records(
        ground_truth,
        signal
    )

    print()
    print(
        f"Events prepared for robustness analysis: "
        f"{len(events)}"
    )

    results = run_analysis(events)

    display_results(results)

    calculate_stability(results)

    results.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print("=" * 75)
    print(
        f"Saved robustness analysis: "
        f"{OUTPUT_FILE.name}"
    )
    print(
        "TEMPORAL ROBUSTNESS ANALYSIS COMPLETE"
    )
    print("=" * 75)


if __name__ == "__main__":
    main()