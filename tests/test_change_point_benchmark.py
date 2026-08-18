from __future__ import annotations

import numpy as np
import pandas as pd

from packages.analytics.change_points import (detect_change_points, consolidate_change_points)


SEED = 42

YEARS = 40
CHANGE_YEAR = 20

TRUE_CHANGE_YEAR = 1980 + CHANGE_YEAR

TOLERANCE = 1

# FIXED detector configuration.
# Do NOT change this according to synthetic magnitude.
MAGNITUDE_THRESHOLD = 0.20
EFFECT_THRESHOLD = 0.50
BEFORE_WINDOW = 3
AFTER_WINDOW = 3
PERSISTENCE_WINDOW = 3


def make_series(
    kind: str,
    magnitude: float,
    noise: float,
    seed: int,
) -> pd.DataFrame:

    rng = np.random.default_rng(seed)

    values = np.zeros(YEARS)

    if kind == "stable":

        values[:] = 0.2

    elif kind == "positive":

        values[:CHANGE_YEAR] = -0.2
        values[CHANGE_YEAR:] = -0.2 + magnitude

    elif kind == "negative":

        values[:CHANGE_YEAR] = 0.2
        values[CHANGE_YEAR:] = 0.2 - magnitude

    elif kind == "temporary":

        values[:] = 0.0

        shock_end = CHANGE_YEAR + 3

        values[
            CHANGE_YEAR:shock_end
        ] = magnitude

    elif kind == "gradual":

        values[:] = 0.0

        for i in range(
            CHANGE_YEAR,
            YEARS,
        ):

            progress = (
                (i - CHANGE_YEAR)
                / (YEARS - CHANGE_YEAR - 1)
            )

            values[i] = magnitude * progress

    else:

        raise ValueError(
            f"Unknown series type: {kind}"
        )

    values += rng.normal(
        0,
        noise,
        YEARS,
    )

    values = np.clip(
        values,
        -1,
        1,
    )

    return pd.DataFrame(
        {
            "country_code": ["SYN"] * YEARS,
            "issue": ["BENCHMARK"] * YEARS,
            "year": np.arange(
                1980,
                1980 + YEARS,
            ),
            "position_score": values,
        }
    )


def extract_detected_years(
    changes: pd.DataFrame,
) -> list[int]:

    if changes is None or changes.empty:
        return []

    if "change_year" not in changes.columns:
        return []

    return sorted(
        pd.to_numeric(
            changes["change_year"],
            errors="coerce",
        )
        .dropna()
        .astype(int)
        .tolist()
    )


def matching_detection(
    detected_years: list[int],
    true_year: int,
    tolerance: int = TOLERANCE,
):

    candidates = [
        year
        for year in detected_years
        if abs(year - true_year) <= tolerance
    ]

    if not candidates:
        return None

    return min(
        candidates,
        key=lambda year:
        abs(year - true_year),
    )


def evaluate_detection(
    detected_years: list[int],
    true_change: bool,
):
    """
    Evaluate one synthetic series.

    For abrupt positive/negative changes:
        TP = detection within tolerance
        FN = missed true change
        FP = additional detections

    Stable:
        every detection is a false positive.
    """

    if not true_change:

        return (
            0,
            len(detected_years),
            0,
            [],
        )

    match = matching_detection(
        detected_years,
        TRUE_CHANGE_YEAR,
    )

    if match is None:

        return (
            0,
            len(detected_years),
            1,
            [],
        )

    extra_detections = [
        year
        for year in detected_years
        if year != match
    ]

    delay = match - TRUE_CHANGE_YEAR

    return (
        1,
        len(extra_detections),
        0,
        [delay],
    )


def main():

    rng = np.random.default_rng(SEED)

    results = []

    magnitudes = [
        0.20,
        0.30,
        0.40,
        0.50,
        0.60,
        0.80,
    ]

    noises = [
        0.00,
        0.05,
        0.10,
        0.15,
    ]

    kinds = [
        "stable",
        "positive",
        "negative",
        "temporary",
        "gradual",
    ]

    repetitions = 20

    print("=" * 90)
    print("CHANGE-POINT SYNTHETIC BENCHMARK")
    print("=" * 90)

    print()
    print("FIXED DETECTOR CONFIGURATION")
    print("-" * 90)
    print(
        "magnitude_threshold:",
        MAGNITUDE_THRESHOLD,
    )
    print(
        "effect_threshold:",
        EFFECT_THRESHOLD,
    )
    print(
        "before_window:",
        BEFORE_WINDOW,
    )
    print(
        "after_window:",
        AFTER_WINDOW,
    )
    print(
        "persistence_window:",
        PERSISTENCE_WINDOW,
    )

    for kind in kinds:

        for magnitude in magnitudes:

            for noise in noises:

                tp = 0
                fp = 0
                fn = 0

                delays = []

                for repetition in range(
                    repetitions
                ):

                    series = make_series(
                        kind=kind,
                        magnitude=magnitude,
                        noise=noise,
                        seed=int(
                            rng.integers(
                                0,
                                1_000_000,
                            )
                        ),
                    )

                    try:

                        changes = (
                            detect_change_points(
                                series,
                                before_window=(
                                    BEFORE_WINDOW
                                ),
                                after_window=(
                                    AFTER_WINDOW
                                ),
                                magnitude_threshold=(
                                    MAGNITUDE_THRESHOLD
                                ),
                                effect_threshold=(
                                    EFFECT_THRESHOLD
                                ),
                                persistence_window=(
                                    PERSISTENCE_WINDOW
                                ),
                            )
                        )
                        changes = consolidate_change_points(
                            changes,
                            min_separation=3,
                        )

                    except Exception as exc:

                        print(
                            "WARNING:",
                            kind,
                            magnitude,
                            noise,
                            type(exc).__name__,
                            exc,
                        )

                        continue

                    detected = (
                        extract_detected_years(
                            changes
                        )
                    )

                    true_change = (
                        kind not in {
                            "stable",
                        }
                    )

                    (
                        local_tp,
                        local_fp,
                        local_fn,
                        local_delays,
                    ) = evaluate_detection(
                        detected,
                        true_change,
                    )

                    tp += local_tp
                    fp += local_fp
                    fn += local_fn

                    delays.extend(
                        local_delays
                    )

                precision = (
                    tp / (tp + fp)
                    if tp + fp > 0
                    else 0.0
                )

                recall = (
                    tp / (tp + fn)
                    if tp + fn > 0
                    else 0.0
                )

                f1 = (
                    2
                    * precision
                    * recall
                    / (precision + recall)
                    if precision + recall > 0
                    else 0.0
                )

                mean_delay = (
                    float(
                        np.mean(delays)
                    )
                    if delays
                    else np.nan
                )

                results.append(
                    {
                        "kind": kind,
                        "magnitude": magnitude,
                        "noise": noise,
                        "tp": tp,
                        "fp": fp,
                        "fn": fn,
                        "precision": precision,
                        "recall": recall,
                        "f1": f1,
                        "mean_detection_delay":
                            mean_delay,
                    }
                )

    result = pd.DataFrame(results)

    print()
    print("=" * 90)
    print("BENCHMARK RESULTS")
    print("=" * 90)

    print(
        result.to_string(
            index=False,
            float_format=lambda x:
            f"{x:.3f}",
        )
    )

    print()
    print("=" * 90)
    print("PERFORMANCE BY SCENARIO")
    print("=" * 90)

    scenario_summary = (
        result
        .groupby("kind")
        .agg(
            precision=("precision", "mean"),
            recall=("recall", "mean"),
            f1=("f1", "mean"),
            mean_delay=(
                "mean_detection_delay",
                "mean",
            ),
            cases=("kind", "size"),
        )
        .reset_index()
    )

    print(
        scenario_summary.to_string(
            index=False,
            float_format=lambda x:
            f"{x:.3f}",
        )
    )

    print()
    print("=" * 90)
    print("PERFORMANCE BY MAGNITUDE")
    print("=" * 90)

    magnitude_summary = (
        result
        .groupby("magnitude")
        .agg(
            precision=("precision", "mean"),
            recall=("recall", "mean"),
            f1=("f1", "mean"),
            mean_delay=(
                "mean_detection_delay",
                "mean",
            ),
            cases=("magnitude", "size"),
        )
        .reset_index()
    )

    print(
        magnitude_summary.to_string(
            index=False,
            float_format=lambda x:
            f"{x:.3f}",
        )
    )

    print()
    print("=" * 90)
    print("PERFORMANCE BY NOISE")
    print("=" * 90)

    noise_summary = (
        result
        .groupby("noise")
        .agg(
            precision=("precision", "mean"),
            recall=("recall", "mean"),
            f1=("f1", "mean"),
            mean_delay=(
                "mean_detection_delay",
                "mean",
            ),
            cases=("noise", "size"),
        )
        .reset_index()
    )

    print(
        noise_summary.to_string(
            index=False,
            float_format=lambda x:
            f"{x:.3f}",
        )
    )

    print()
    print("=" * 90)
    print("AGGREGATE PERFORMANCE")
    print("=" * 90)

    total_tp = int(
        result["tp"].sum()
    )

    total_fp = int(
        result["fp"].sum()
    )

    total_fn = int(
        result["fn"].sum()
    )

    precision = (
        total_tp
        / (total_tp + total_fp)
        if total_tp + total_fp > 0
        else 0.0
    )

    recall = (
        total_tp
        / (total_tp + total_fn)
        if total_tp + total_fn > 0
        else 0.0
    )

    f1 = (
        2
        * precision
        * recall
        / (precision + recall)
        if precision + recall > 0
        else 0.0
    )

    print("Total TP:", total_tp)
    print("Total FP:", total_fp)
    print("Total FN:", total_fn)

    print(
        "Overall precision:",
        round(precision, 3),
    )

    print(
        "Overall recall:",
        round(recall, 3),
    )

    print(
        "Overall F1:",
        round(f1, 3),
    )

    valid_delay = result[
        result[
            "mean_detection_delay"
        ].notna()
    ]

    if not valid_delay.empty:

        print(
            "Mean detection delay:",
            round(
                valid_delay[
                    "mean_detection_delay"
                ].mean(),
                3,
            ),
            "years",
        )

    output = (
        "change_point_benchmark.csv"
    )

    result.to_csv(
        output,
        index=False,
    )

    print()
    print(
        f"Saved benchmark: {output}"
    )

    print()
    print("=" * 90)
    print(
        "CHANGE-POINT BENCHMARK COMPLETE"
    )
    print("=" * 90)


if __name__ == "__main__":
    main()