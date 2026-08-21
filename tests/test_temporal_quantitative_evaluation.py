import os
import pandas as pd
import numpy as np


GROUND_TRUTH = "data/validation/temporal_ground_truth.csv"
DETECTED = "temporal_alignment_change_points.csv"
EPISODES = "temporal_alignment_change_episodes.csv"

OUTPUT = "temporal_quantitative_evaluation.csv"


def normalize_pair(a, b):
    return tuple(sorted([str(a).strip(), str(b).strip()]))


def load_ground_truth():
    if not os.path.exists(GROUND_TRUTH):
        raise FileNotFoundError(
            f"Missing ground truth file: {GROUND_TRUTH}"
        )

    df = pd.read_csv(GROUND_TRUTH)

    required = [
        "country_a",
        "country_b",
        "event_start",
        "event_end",
    ]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(
            f"Ground truth missing columns: {missing}"
        )

    df = df.copy()

    df["country_a"] = df["country_a"].astype(str).str.strip()
    df["country_b"] = df["country_b"].astype(str).str.strip()

    df["event_start"] = pd.to_numeric(
        df["event_start"], errors="coerce"
    )

    df["event_end"] = pd.to_numeric(
        df["event_end"], errors="coerce"
    )

    df = df.dropna(
        subset=["event_start", "event_end"]
    )

    df["pair"] = df.apply(
        lambda r: normalize_pair(
            r["country_a"],
            r["country_b"]
        ),
        axis=1,
    )

    return df


def load_detected_events():
    """
    Load detected change points.

    We prefer change points because they represent the
    individual detected temporal events.
    """

    if not os.path.exists(DETECTED):
        raise FileNotFoundError(
            f"Missing detected change-point file: {DETECTED}"
        )

    df = pd.read_csv(DETECTED)

    required = [
        "country_a",
        "country_b",
        "change_year",
    ]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(
            f"Detected file missing columns: {missing}"
        )

    df = df.copy()

    df["country_a"] = df["country_a"].astype(str).str.strip()
    df["country_b"] = df["country_b"].astype(str).str.strip()

    df["change_year"] = pd.to_numeric(
        df["change_year"],
        errors="coerce"
    )

    df = df.dropna(subset=["change_year"])

    df["pair"] = df.apply(
        lambda r: normalize_pair(
            r["country_a"],
            r["country_b"]
        ),
        axis=1,
    )

    return df


def match_events_one_to_one(
    ground_truth,
    detected,
    tolerance
):
    """
    One-to-one temporal matching within the SAME country pair.

    A detection is valid only when the country pair is identical
    and the detection is within the requested temporal tolerance.
    Each ground-truth event and detection can be used only once.
    """

    matches = []
    used_gt = set()
    used_detected = set()
    candidates = []

    for gt_idx, gt in ground_truth.iterrows():
        gt_year = int(gt["event_start"])
        gt_pair = gt["pair"]

        for det_idx, det in detected.iterrows():
            det_year = int(det["change_year"])
            det_pair = det["pair"]

            if gt_pair != det_pair:
                continue

            error = det_year - gt_year
            absolute_error = abs(error)

            if absolute_error > tolerance:
                continue

            candidates.append({
                "gt_index": gt_idx,
                "detected_index": det_idx,
                "pair": gt_pair,
                "event_start": gt_year,
                "detected_year": det_year,
                "error": error,
                "absolute_error": absolute_error,
            })

    candidates.sort(key=lambda x: x["absolute_error"])

    for candidate in candidates:
        gt_idx = candidate["gt_index"]
        det_idx = candidate["detected_index"]

        if gt_idx in used_gt or det_idx in used_detected:
            continue

        used_gt.add(gt_idx)
        used_detected.add(det_idx)
        matches.append({**candidate, "matched": True})

    for gt_idx, gt in ground_truth.iterrows():
        if gt_idx not in used_gt:
            matches.append({
                "gt_index": gt_idx,
                "detected_index": np.nan,
                "pair": gt["pair"],
                "event_start": int(gt["event_start"]),
                "detected_year": np.nan,
                "error": np.nan,
                "absolute_error": np.nan,
                "matched": False,
            })

    for det_idx, det in detected.iterrows():
        if det_idx not in used_detected:
            matches.append({
                "gt_index": np.nan,
                "detected_index": det_idx,
                "pair": det["pair"],
                "event_start": np.nan,
                "detected_year": int(det["change_year"]),
                "error": np.nan,
                "absolute_error": np.nan,
                "matched": False,
            })

    return pd.DataFrame(matches)


def calculate_metrics(
    ground_truth,
    detected,
    matches,
    used_detected,
    tolerance,
):
    total_gt = len(ground_truth)
    total_detected = len(detected)

    if "absolute_error" not in matches.columns:
        matches["absolute_error"] = np.nan

    # A detection counts as a true positive ONLY if it
    # falls inside the requested tolerance window.
    valid_matches = matches[
        (matches["matched"] == True)
        & (matches["absolute_error"] <= tolerance)
    ].copy()

    true_positive = len(valid_matches)

    # Ground-truth events without a valid detection.
    false_negative = total_gt - true_positive

    # Only detections actually used by valid matches
    # are true positives. Everything else is a false positive.
    valid_detected_indices = set(
        valid_matches["detected_index"].dropna().tolist()
    )

    false_positive = (
        total_detected - len(valid_detected_indices)
    )

    precision = (
        true_positive /
        (true_positive + false_positive)
        if (true_positive + false_positive) > 0
        else 0.0
    )

    recall = (
        true_positive / total_gt
        if total_gt > 0
        else 0.0
    )

    f1 = (
        2 * precision * recall /
        (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    if len(valid_matches) > 0:

        mean_error = (
            valid_matches["absolute_error"]
            .mean()
        )

        median_error = (
            valid_matches["absolute_error"]
            .median()
        )

    else:

        mean_error = np.nan
        median_error = np.nan

    return {
        "tolerance_years": tolerance,
        "ground_truth_events": total_gt,
        "detected_events": total_detected,
        "true_positives": true_positive,
        "false_positives": false_positive,
        "false_negatives": false_negative,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "mean_absolute_error": mean_error,
        "median_absolute_error": median_error,
    }

def match_events(
    ground_truth,
    detected,
    tolerance=5,
):
    """
    Compatibility wrapper around the one-to-one matcher.

    Returns:
        matches: DataFrame containing matched and unmatched events
        used_detected: set of detected-event indices that were matched
    """

    matches = match_events_one_to_one(
        ground_truth,
        detected,
        tolerance=tolerance,
    )

    used_detected = set(
        matches.loc[
            matches["matched"] == True,
            "detected_index"
        ]
        .dropna()
        .tolist()
    )

    return matches, used_detected

def evaluate_by_pair(
    ground_truth,
    detected,
    tolerance=5,
):
    pairs = sorted(
        set(ground_truth["pair"])
        | set(detected["pair"])
    )

    rows = []

    for pair in pairs:

        gt_pair = ground_truth[
            ground_truth["pair"] == pair
        ]

        det_pair = detected[
            detected["pair"] == pair
        ]

        pair_matches, used = match_events(
            gt_pair,
            det_pair,
            tolerance=tolerance,
        )

        metrics = calculate_metrics(
            gt_pair,
            det_pair,
            pair_matches,
            used,
            tolerance,
        )

        metrics["country_a"] = pair[0]
        metrics["country_b"] = pair[1]

        rows.append(metrics)

    return pd.DataFrame(rows)


def main():

    print("=" * 80)
    print("TEMPORAL QUANTITATIVE EVALUATION")
    print("=" * 80)

    ground_truth = load_ground_truth()
    detected = load_detected_events()

    print()
    print(f"Ground-truth events: {len(ground_truth)}")
    print(f"Detected change points: {len(detected)}")

    matches, used_detected = match_events(
    ground_truth,
    detected,
    tolerance=5,
    )

    print()
    print("=" * 80)
    print("DETECTION TOLERANCE SCORECARD")
    print("=" * 80)

    all_metrics = []

    for tolerance in [0, 1, 3, 5]:

        metrics = calculate_metrics(
            ground_truth,
            detected,
            matches,
            used_detected,
            tolerance,
        )

        all_metrics.append(metrics)

        print()
        print(
            f"Tolerance: ±{tolerance} year"
        )

        print(
            f"  Precision: "
            f"{metrics['precision']:.3f}"
        )

        print(
            f"  Recall:    "
            f"{metrics['recall']:.3f}"
        )

        print(
            f"  F1:        "
            f"{metrics['f1']:.3f}"
        )

        print(
            f"  TP: {metrics['true_positives']} "
            f"FP: {metrics['false_positives']} "
            f"FN: {metrics['false_negatives']}"
        )

    scorecard = pd.DataFrame(all_metrics)

    scorecard.to_csv(
        OUTPUT,
        index=False
    )

    print()
    print("=" * 80)
    print("ERROR ANALYSIS")
    print("=" * 80)

    matched = matches[
        matches["matched"] == True
    ]

    if not matched.empty:

        print(
            f"Matched events: {len(matched)}"
        )

        print(
            f"Mean absolute detection error: "
            f"{matched['absolute_error'].mean():.3f} years"
        )

        print(
            f"Median absolute detection error: "
            f"{matched['absolute_error'].median():.3f} years"
        )

        print()
        print("Matched events:")

        print(
            matched[
                [
                    "pair",
                    "event_start",
                    "detected_year",
                    "error",
                    "absolute_error",
                ]
            ].to_string(index=False)
        )

    print()
    print("=" * 80)
    print("COUNTRY-PAIR PERFORMANCE (±5 YEARS)")
    print("=" * 80)

    pair_results = evaluate_by_pair(
        ground_truth,
        detected,
        tolerance=5,
    )

    print(
        pair_results[
            [
                "country_a",
                "country_b",
                "ground_truth_events",
                "detected_events",
                "true_positives",
                "false_positives",
                "false_negatives",
                "precision",
                "recall",
                "f1",
            ]
        ].to_string(index=False)
    )

    pair_results.to_csv(
        "temporal_quantitative_by_pair.csv",
        index=False
    )

    print()
    print("=" * 80)
    print("QUANTITATIVE EVALUATION COMPLETE")
    print("=" * 80)

    print()
    print(f"Saved scorecard: {OUTPUT}")
    print(
        "Saved pair evaluation: "
        "temporal_quantitative_by_pair.csv"
    )


if __name__ == "__main__":
    main()