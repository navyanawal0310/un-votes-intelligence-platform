"""
UN Votes Analyzer
Temporal Null / Chance Baseline

Purpose:
    Compare observed historical-event detections against detections
    obtained when event years are randomly shifted.

This is a baseline test, NOT an optimization procedure.

The same:
    - country pairs
    - event signal
    - signal threshold
    - detection tolerance

are retained.

Only the event timing is randomized.
"""

from pathlib import Path
import numpy as np
import pandas as pd


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

OUTPUT_FILE = (
    BASE_DIR
    / "temporal_null_baseline.csv"
)

# Keep this deliberately moderate.
N_TRIALS = 100

# Primary operating point.
SIGNAL_THRESHOLD = 0.05
DETECTION_TOLERANCE = 5

# Random event years must stay inside this historical range.
MIN_YEAR = 1946
MAX_YEAR = 2025

RANDOM_SEED = 42


# ============================================================
# HELPERS
# ============================================================

def find_column(df, candidates, required=True):

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
    print("TEMPORAL NULL / CHANCE BASELINE")
    print("=" * 75)

    if not GROUND_TRUTH_FILE.exists():
        raise FileNotFoundError(
            f"Missing ground truth file:\n"
            f"{GROUND_TRUTH_FILE}"
        )

    if not SIGNAL_FILE.exists():
        raise FileNotFoundError(
            f"Missing signal file:\n"
            f"{SIGNAL_FILE}"
        )

    ground_truth = pd.read_csv(
        GROUND_TRUTH_FILE
    )

    signal = pd.read_csv(
        SIGNAL_FILE
    )

    print()
    print(
        f"Ground-truth events: {len(ground_truth)}"
    )

    print(
        f"Signal observations: {len(signal)}"
    )

    return ground_truth, signal


# ============================================================
# PREPARE GROUND TRUTH
# ============================================================

def prepare_ground_truth(df):

    df = df.copy()

    country_a = find_column(
        df,
        ["country_a"]
    )

    country_b = find_column(
        df,
        ["country_b"]
    )

    event_start = find_column(
        df,
        [
            "event_start",
            "event_year",
            "start_year"
        ]
    )

    event_end = find_column(
        df,
        [
            "event_end",
            "end_year"
        ],
        required=False
    )

    df["pair"] = [
        normalize_pair(a, b)
        for a, b in zip(
            df[country_a],
            df[country_b]
        )
    ]

    df["event_start_year"] = pd.to_numeric(
        df[event_start],
        errors="coerce"
    )

    if event_end:

        df["event_end_year"] = pd.to_numeric(
            df[event_end],
            errors="coerce"
        )

    else:

        df["event_end_year"] = (
            df["event_start_year"]
        )

    df["event_end_year"] = (
        df["event_end_year"]
        .fillna(df["event_start_year"])
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

    country_a = find_column(
        df,
        ["country_a"]
    )

    country_b = find_column(
        df,
        ["country_b"]
    )

    event_start = find_column(
        df,
        [
            "event_start",
            "event_year",
            "start_year"
        ]
    )

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
        for a, b in zip(
            df[country_a],
            df[country_b]
        )
    ]

    df["event_start_year"] = pd.to_numeric(
        df[event_start],
        errors="coerce"
    )

    df["signal_value"] = pd.to_numeric(
        df[signal_column],
        errors="coerce"
    ).abs()

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
# BUILD OBSERVED EVENT RECORDS
# ============================================================

def build_event_records(
    ground_truth,
    signal
):

    records = []

    for _, gt in ground_truth.iterrows():

        pair = gt["pair"]
        event_year = gt["event_start_year"]

        candidates = signal[
            (signal["pair"] == pair)
            &
            (
                signal["event_start_year"]
                == event_year
            )
        ].copy()

        # Fallback:
        # find the closest signal observation for
        # this country pair.
        if candidates.empty:

            pair_candidates = signal[
                signal["pair"] == pair
            ].copy()

            if not pair_candidates.empty:

                pair_candidates["year_distance"] = (
                    pair_candidates[
                        "event_start_year"
                    ]
                    - event_year
                ).abs()

                candidates = (
                    pair_candidates
                    .sort_values("year_distance")
                    .head(1)
                )

        if candidates.empty:

            records.append({
                "pair": pair,
                "observed_event_year": event_year,
                "signal": np.nan,
                "detected_year": np.nan
            })

            continue

        row = candidates.iloc[0]

        records.append({
            "pair": pair,
            "observed_event_year": event_year,
            "signal": row["signal_value"],
            "detected_year": row["detected_year"]
        })

    return pd.DataFrame(records)


# ============================================================
# OBSERVED DETECTION
# ============================================================

def calculate_observed_detection(
    events,
    threshold,
    tolerance
):

    measurable = events[
        events["signal"].notna()
        &
        (
            events["signal"]
            >= threshold
        )
    ].copy()

    detected = measurable[
        measurable["detected_year"].notna()
    ].copy()

    if detected.empty:

        detected_count = 0

    else:

        detected["distance"] = (
            detected["detected_year"]
            - detected["observed_event_year"]
        ).abs()

        detected_count = int(
            (
                detected["distance"]
                <= tolerance
            ).sum()
        )

    total = len(events)

    return {
        "total_events": total,
        "measurable_events": len(measurable),
        "detected_events": detected_count,
        "detection_rate": safe_divide(
            detected_count,
            total
        )
    }


# ============================================================
# NULL DETECTION
# ============================================================

def calculate_null_detection(
    events,
    signal,
    rng,
    threshold,
    tolerance
):
    """
    Randomly assign an event year to each historical event.

    Country-pair identity is preserved.

    A random event is considered detected if a change point
    for that same country pair lies within the specified
    tolerance of the randomized event year.

    The observed event signal is NOT used to decide whether
    a random event is measurable. This prevents leakage from
    the observed event timing.

    Instead, the null asks:

        "How often would a random event date happen to fall
         near an existing change point?"
    """

    detections = 0
    random_events = len(events)

    for _, event in events.iterrows():

        pair = event["pair"]

        random_year = rng.integers(
            MIN_YEAR,
            MAX_YEAR + 1
        )

        pair_signal = signal[
            signal["pair"] == pair
        ].copy()

        if pair_signal.empty:
            continue

        change_years = pd.to_numeric(
            pair_signal["detected_year"],
            errors="coerce"
        ).dropna()

        if change_years.empty:
            continue

        distances = (
            change_years
            - random_year
        ).abs()

        if (
            distances
            .min()
            <= tolerance
        ):
            detections += 1

    return safe_divide(
        detections,
        random_events
    )


# ============================================================
# RUN NULL SIMULATION
# ============================================================

def run_null_simulation(
    events,
    signal
):

    rng = np.random.default_rng(
        RANDOM_SEED
    )

    results = []

    print()
    print(
        f"Running {N_TRIALS} random trials..."
    )

    for trial in range(
        1,
        N_TRIALS + 1
    ):

        rate = calculate_null_detection(
            events,
            signal,
            rng,
            SIGNAL_THRESHOLD,
            DETECTION_TOLERANCE
        )

        results.append({
            "trial": trial,
            "random_detection_rate": rate
        })

    return pd.DataFrame(results)


# ============================================================
# SUMMARY
# ============================================================

def summarize(
    observed,
    null_results
):

    rates = (
        null_results[
            "random_detection_rate"
        ]
        .astype(float)
    )

    mean_null = rates.mean()
    median_null = rates.median()

    percentile_95 = np.percentile(
        rates,
        95
    )

    percentile_99 = np.percentile(
        rates,
        99
    )

    observed_rate = (
        observed["detection_rate"]
    )

    excess = (
        observed_rate
        - mean_null
    )

    # Empirical one-sided p-value:
    # proportion of null trials at least
    # as large as the observed rate.
    p_value = (
        (rates >= observed_rate).sum()
        + 1
    ) / (
        len(rates) + 1
    )

    print()
    print("=" * 75)
    print("OBSERVED VS NULL BASELINE")
    print("=" * 75)

    print()
    print("OBSERVED HISTORICAL EVENTS")
    print(
        f"Total events: "
        f"{observed['total_events']}"
    )

    print(
        f"Measurable events: "
        f"{observed['measurable_events']}"
    )

    print(
        f"Detected events: "
        f"{observed['detected_events']}"
    )

    print(
        f"Observed detection rate: "
        f"{observed_rate:.3f}"
    )

    print()
    print("NULL RANDOM BASELINE")

    print(
        f"Trials: {len(rates)}"
    )

    print(
        f"Mean random detection rate: "
        f"{mean_null:.3f}"
    )

    print(
        f"Median random detection rate: "
        f"{median_null:.3f}"
    )

    print(
        f"95th percentile: "
        f"{percentile_95:.3f}"
    )

    print(
        f"99th percentile: "
        f"{percentile_99:.3f}"
    )

    print()
    print("COMPARISON")

    print(
        f"Observed rate: "
        f"{observed_rate:.3f}"
    )

    print(
        f"Null mean: "
        f"{mean_null:.3f}"
    )

    print(
        f"Observed excess over null: "
        f"{excess:.3f}"
    )

    print(
        f"Empirical one-sided p-value: "
        f"{p_value:.3f}"
    )

    print()
    print("INTERPRETATION")

    if observed_rate > percentile_95:

        print(
            "Observed detection rate is above "
            "the 95th percentile of the null baseline."
        )

    elif observed_rate > mean_null:

        print(
            "Observed detection rate is above the "
            "null mean, but not beyond the 95th "
            "percentile."
        )

    else:

        print(
            "Observed detection rate is not above "
            "the null baseline."
        )

    print()
    print(
        "This test does NOT establish causality."
    )

    print(
        "It evaluates whether observed temporal "
        "co-occurrence is stronger than a simple "
        "random-timing baseline."
    )

    return {
        "observed_detection_rate": observed_rate,
        "null_mean": mean_null,
        "null_median": median_null,
        "null_95th_percentile": percentile_95,
        "null_99th_percentile": percentile_99,
        "observed_excess": excess,
        "empirical_p_value": p_value
    }


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

    events = build_event_records(
        ground_truth,
        signal
    )

    print()
    print(
        f"Events prepared: {len(events)}"
    )

    print(
        f"Signal threshold: "
        f"{SIGNAL_THRESHOLD:.3f}"
    )

    print(
        f"Detection tolerance: "
        f"±{DETECTION_TOLERANCE} years"
    )

    observed = calculate_observed_detection(
        events,
        SIGNAL_THRESHOLD,
        DETECTION_TOLERANCE
    )

    null_results = run_null_simulation(
        events,
        signal
    )

    summary = summarize(
        observed,
        null_results
    )

    # Save trial-level results plus
    # the overall summary.
    output = null_results.copy()

    for key, value in summary.items():
        output[key] = value

    output["signal_threshold"] = (
        SIGNAL_THRESHOLD
    )

    output["detection_tolerance"] = (
        DETECTION_TOLERANCE
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print("=" * 75)
    print(
        f"Saved null baseline: "
        f"{OUTPUT_FILE.name}"
    )

    print(
        "TEMPORAL NULL BASELINE COMPLETE"
    )
    print("=" * 75)


if __name__ == "__main__":
    main()