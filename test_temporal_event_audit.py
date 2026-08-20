from pathlib import Path
import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parent

GROUND_TRUTH_PATH = (
    ROOT / "data" / "validation" / "temporal_ground_truth.csv"
)

CHANGE_POINTS_PATH = (
    ROOT / "temporal_alignment_change_points.csv"
)

OUTPUT_PATH = (
    ROOT / "temporal_event_audit.csv"
)

PRE_EVENT_WINDOW = 3
NEAR_EVENT_TOLERANCE = 5
STRONG_SHIFT_THRESHOLD = 0.10
PERSISTENCE_WINDOW = 2


# ============================================================
# LOADERS
# ============================================================

def load_ground_truth():
    if not GROUND_TRUTH_PATH.exists():
        raise FileNotFoundError(
            f"Missing ground truth: {GROUND_TRUTH_PATH}"
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
            f"Ground truth missing columns: {missing}"
        )

    df["event_start"] = pd.to_numeric(
        df["event_start"], errors="coerce"
    )
    df["event_end"] = pd.to_numeric(
        df["event_end"], errors="coerce"
    )

    return df


def load_change_points():
    if not CHANGE_POINTS_PATH.exists():
        raise FileNotFoundError(
            f"Missing change-point file: {CHANGE_POINTS_PATH}"
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
            f"Change-point file missing columns: {missing}"
        )

    df["change_year"] = pd.to_numeric(
        df["change_year"],
        errors="coerce",
    )

    return df.dropna(
        subset=["change_year"]
    ).copy()


# ============================================================
# ALIGNMENT SERIES
# ============================================================

def get_alignment_file(country_a, country_b):
    candidates = [
        ROOT / f"alignment_{country_a}_{country_b}.csv",
        ROOT / f"alignment_{country_b}_{country_a}.csv",
    ]

    for path in candidates:
        if path.exists():
            return path

    return None


def load_alignment(country_a, country_b):

    path = get_alignment_file(
        country_a,
        country_b,
    )

    if path is None:
        return None

    df = pd.read_csv(path)

    if "year" not in df.columns:
        return None

    if "alignment_score" not in df.columns:
        return None

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df["alignment_score"] = pd.to_numeric(
        df["alignment_score"],
        errors="coerce",
    )

    df = df.dropna(
        subset=["year", "alignment_score"]
    ).copy()

    return df.sort_values("year")


# ============================================================
# SIGNAL ANALYSIS
# ============================================================

def calculate_signal(
    df,
    event_start,
    event_end,
):

    if df is None or df.empty:
        return {
            "pre_observations": 0,
            "event_observations": 0,
            "pre_mean": np.nan,
            "event_mean": np.nan,
            "absolute_shift": np.nan,
            "local_max_change": np.nan,
            "persistent_shift": False,
        }

    pre = df[
        (df["year"] >= event_start - PRE_EVENT_WINDOW)
        & (df["year"] < event_start)
    ]

    event = df[
        (df["year"] >= event_start)
        & (df["year"] <= event_end)
    ]

    pre_mean = (
        pre["alignment_score"].mean()
        if not pre.empty
        else np.nan
    )

    event_mean = (
        event["alignment_score"].mean()
        if not event.empty
        else np.nan
    )

    if pd.notna(pre_mean) and pd.notna(event_mean):
        absolute_shift = abs(
            event_mean - pre_mean
        )
    else:
        absolute_shift = np.nan

    # --------------------------------------------------------
    # LOCAL ANNUAL CHANGES
    # --------------------------------------------------------

    local = df[
        (df["year"] >= event_start - PRE_EVENT_WINDOW)
        & (
            df["year"]
            <= event_end + PRE_EVENT_WINDOW
        )
    ].copy()

    local["annual_change"] = (
        local["alignment_score"]
        .diff()
        .abs()
    )

    local_max_change = (
        local["annual_change"].max()
        if not local.empty
        else np.nan
    )

    # --------------------------------------------------------
    # PERSISTENCE
    # --------------------------------------------------------

    persistent_shift = False

    if (
        pd.notna(pre_mean)
        and not event.empty
    ):

        event_values = event[
            "alignment_score"
        ].values

        if len(event_values) >= PERSISTENCE_WINDOW:

            differences = np.abs(
                event_values - pre_mean
            )

            for i in range(
                len(differences)
                - PERSISTENCE_WINDOW
                + 1
            ):

                window = differences[
                    i:
                    i + PERSISTENCE_WINDOW
                ]

                if np.all(
                    window >= STRONG_SHIFT_THRESHOLD
                ):
                    persistent_shift = True
                    break

    return {
        "pre_observations": len(pre),
        "event_observations": len(event),
        "pre_mean": pre_mean,
        "event_mean": event_mean,
        "absolute_shift": absolute_shift,
        "local_max_change": local_max_change,
        "persistent_shift": persistent_shift,
    }


# ============================================================
# CHANGE-POINT ANALYSIS
# ============================================================

def get_pair_change_points(
    change_points,
    country_a,
    country_b,
):

    forward = (
        (change_points["country_a"] == country_a)
        &
        (change_points["country_b"] == country_b)
    )

    reverse = (
        (change_points["country_a"] == country_b)
        &
        (change_points["country_b"] == country_a)
    )

    return change_points[
        forward | reverse
    ].copy()


def nearest_change_point(
    pair_points,
    event_start,
    event_end,
):

    if pair_points.empty:
        return None

    points = pair_points.copy()

    def distance(year):

        if event_start <= year <= event_end:
            return 0

        if year < event_start:
            return event_start - year

        return year - event_end

    points["distance"] = (
        points["change_year"]
        .apply(distance)
    )

    points = points.sort_values(
        [
            "distance",
            "confidence",
        ],
        ascending=[True, False],
    )

    return points.iloc[0]


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_event(
    signal,
    nearest,
):

    if signal["pre_observations"] == 0:
        return "NO_PRE_EVENT_DATA"

    if signal["event_observations"] == 0:
        return "NO_EVENT_DATA"

    if pd.isna(
        signal["absolute_shift"]
    ):
        return "NO_MEASURABLE_SIGNAL"

    if signal["absolute_shift"] < STRONG_SHIFT_THRESHOLD:

        if nearest is None:
            return "WEAK_SIGNAL_NO_DETECTION"

        if nearest["distance"] <= NEAR_EVENT_TOLERANCE:
            return "WEAK_SIGNAL_NEAR_DETECTION"

        return "WEAK_SIGNAL_FAR_DETECTION"

    # Strong signal exists.

    if nearest is None:
        return "STRONG_SIGNAL_NO_DETECTION"

    if nearest["distance"] == 0:
        return "STRONG_SIGNAL_EXACT_DETECTION"

    if nearest["distance"] <= NEAR_EVENT_TOLERANCE:
        return "STRONG_SIGNAL_NEAR_DETECTION"

    return "STRONG_SIGNAL_FAR_DETECTION"


# ============================================================
# MAIN AUDIT
# ============================================================

def main():

    print()
    print("=" * 90)
    print("TEMPORAL EVENT AUDIT")
    print("=" * 90)

    ground_truth = load_ground_truth()
    change_points = load_change_points()

    print(
        f"\nHistorical events: "
        f"{len(ground_truth)}"
    )

    print(
        f"Candidate change points: "
        f"{len(change_points)}"
    )

    rows = []

    for _, event in ground_truth.iterrows():

        country_a = str(
            event["country_a"]
        ).strip()

        country_b = str(
            event["country_b"]
        ).strip()

        event_start = int(
            event["event_start"]
        )

        event_end = int(
            event["event_end"]
        )

        # ----------------------------------------------------
        # LOAD SERIES
        # ----------------------------------------------------

        alignment = load_alignment(
            country_a,
            country_b,
        )

        signal = calculate_signal(
            alignment,
            event_start,
            event_end,
        )

        # ----------------------------------------------------
        # CHANGE POINTS
        # ----------------------------------------------------

        pair_points = get_pair_change_points(
            change_points,
            country_a,
            country_b,
        )

        nearest = nearest_change_point(
            pair_points,
            event_start,
            event_end,
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
                nearest["distance"]
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

        # ----------------------------------------------------
        # CLASSIFICATION
        # ----------------------------------------------------

        classification = classify_event(
            signal,
            nearest,
        )

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        rows.append({

            "country_a": country_a,
            "country_b": country_b,

            "event_start": event_start,
            "event_end": event_end,

            "event_name": event[
                "event_name"
            ],

            "pre_observations":
                signal["pre_observations"],

            "event_observations":
                signal["event_observations"],

            "pre_mean":
                signal["pre_mean"],

            "event_mean":
                signal["event_mean"],

            "absolute_shift":
                signal["absolute_shift"],

            "local_max_change":
                signal["local_max_change"],

            "persistent_shift":
                signal["persistent_shift"],

            "nearest_change_year":
                nearest_year,

            "detection_distance":
                distance,

            "change_point_magnitude":
                magnitude,

            "change_point_effect_size":
                effect_size,

            "change_point_confidence":
                confidence,

            "change_point_confirmed":
                confirmed,

            "classification":
                classification,
        })

    results = pd.DataFrame(rows)

    # ========================================================
    # SUMMARY
    # ========================================================

    measurable = results[
        results["absolute_shift"].notna()
    ]

    strong_signal = results[
        results["absolute_shift"]
        >= STRONG_SHIFT_THRESHOLD
    ]

    exact = results[
        results["detection_distance"] == 0
    ]

    near = results[
        results["detection_distance"]
        <= NEAR_EVENT_TOLERANCE
    ]

    print()
    print("=" * 90)
    print("AUDIT SUMMARY")
    print("=" * 90)

    print(
        f"Events evaluated: "
        f"{len(results)}"
    )

    print(
        f"Events with measurable signal: "
        f"{len(measurable)}"
        f" / {len(results)}"
    )

    print(
        f"Events with strong signal "
        f"(shift >= {STRONG_SHIFT_THRESHOLD:.2f}): "
        f"{len(strong_signal)}"
    )

    print(
        f"Exact detections: "
        f"{len(exact)}"
    )

    print(
        f"Detections within "
        f"{NEAR_EVENT_TOLERANCE} years: "
        f"{len(near)}"
    )

    print()

    print(
        f"Signal availability: "
        f"{len(measurable) / len(results):.3f}"
    )

    print(
        f"Strong-signal rate: "
        f"{len(strong_signal) / len(results):.3f}"
    )

    print(
        f"Exact detection rate: "
        f"{len(exact) / len(results):.3f}"
    )

    print(
        f"±{NEAR_EVENT_TOLERANCE}-year detection rate: "
        f"{len(near) / len(results):.3f}"
    )

    # ========================================================
    # CLASSIFICATION DISTRIBUTION
    # ========================================================

    print()
    print("=" * 90)
    print("EVENT CLASSIFICATIONS")
    print("=" * 90)

    classification_counts = (
        results["classification"]
        .value_counts()
    )

    for label, count in (
        classification_counts.items()
    ):
        print(
            f"{label}: {count}"
        )

    # ========================================================
    # EVENT TABLE
    # ========================================================

    print()
    print("=" * 90)
    print("EVENT AUDIT")
    print("=" * 90)

    display_columns = [
        "country_a",
        "country_b",
        "event_start",
        "event_end",
        "event_name",
        "pre_observations",
        "event_observations",
        "pre_mean",
        "event_mean",
        "absolute_shift",
        "local_max_change",
        "nearest_change_year",
        "detection_distance",
        "change_point_confidence",
        "classification",
    ]

    display = results[
        display_columns
    ].copy()

    numeric_columns = [
        "pre_mean",
        "event_mean",
        "absolute_shift",
        "local_max_change",
        "detection_distance",
        "change_point_confidence",
    ]

    for column in numeric_columns:
        display[column] = display[
            column
        ].round(3)

    print(
        display.to_string(index=False)
    )

    # ========================================================
    # SAVE
    # ========================================================

    results.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print()
    print(
        f"Saved audit to: "
        f"{OUTPUT_PATH.name}"
    )

    print()
    print("=" * 90)
    print(
        "TEMPORAL EVENT AUDIT COMPLETE"
    )
    print("=" * 90)


if __name__ == "__main__":
    main()