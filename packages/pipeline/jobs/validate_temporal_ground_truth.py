from __future__ import annotations

from pathlib import Path

import pandas as pd

from packages.pipeline.transformation.analytical_artifacts import (
    load_change_points,
)


BASE_DIR = Path(__file__).resolve().parents[3]

GROUND_TRUTH = (
    BASE_DIR / "data" / "validation" / "temporal_ground_truth.csv"
)

OUTPUT = (
    BASE_DIR
    / "data"
    / "gold"
    / "analytical"
    / "temporal_ground_truth_validation.csv"
)


TOLERANCE_YEARS = 5


def normalize_pair(a: str, b: str) -> tuple[str, str]:
    return tuple(
        sorted(
            [
                str(a).strip().upper(),
                str(b).strip().upper(),
            ]
        )
    )


def event_distance(
    year: int,
    start: int,
    end: int,
) -> int:

    if start <= year <= end:
        return 0

    if year < start:
        return start - year

    return year - end


def main() -> None:

    print("=" * 80)
    print("UN VOTES ANALYZER — TEMPORAL GROUND-TRUTH VALIDATION")
    print("=" * 80)

    if not GROUND_TRUTH.exists():
        raise FileNotFoundError(
            f"Ground truth not found: {GROUND_TRUTH}"
        )

    ground_truth = pd.read_csv(
        GROUND_TRUTH
    )

    required = {
        "country_a",
        "country_b",
        "event_start",
        "event_end",
        "event_name",
    }

    missing = required - set(
        ground_truth.columns
    )

    if missing:
        raise ValueError(
            f"Ground truth missing columns: {sorted(missing)}"
        )

    changes = load_change_points()

    print(
        f"\nGround-truth events: {len(ground_truth)}"
    )

    print(
        f"Change-point detections: {len(changes):,}"
    )

    results = []

    for _, event in ground_truth.iterrows():

        a = str(event["country_a"]).strip().upper()
        b = str(event["country_b"]).strip().upper()

        start = int(event["event_start"])
        end = int(event["event_end"])

        pair = changes[
            changes.apply(
                lambda row:
                    normalize_pair(
                        row["country_a"],
                        row["country_b"],
                    )
                    == normalize_pair(a, b),
                axis=1,
            )
        ].copy()

        if pair.empty:

            results.append(
                {
                    "country_a": a,
                    "country_b": b,
                    "event_start": start,
                    "event_end": end,
                    "event_name": event["event_name"],
                    "nearest_change_year": None,
                    "detection_distance": None,
                    "detected_strict": False,
                    "detected_tolerance": False,
                }
            )

            continue

        pair["distance"] = pair[
            "change_year"
        ].apply(
            lambda year:
                event_distance(
                    int(year),
                    start,
                    end,
                )
        )

        nearest = pair.sort_values(
            [
                "distance",
                "confidence",
            ],
            ascending=[
                True,
                False,
            ],
        ).iloc[0]

        distance = int(
            nearest["distance"]
        )

        results.append(
            {
                "country_a": a,
                "country_b": b,
                "event_start": start,
                "event_end": end,
                "event_name": event["event_name"],
                "nearest_change_year":
                    int(nearest["change_year"]),
                "detection_distance":
                    distance,
                "change_magnitude":
                    float(nearest["change_magnitude"]),
                "effect_size":
                    float(nearest["effect_size"]),
                "confidence":
                    float(nearest["confidence"]),
                "confirmed":
                    bool(nearest["confirmed"]),
                "detected_strict":
                    distance == 0,
                "detected_tolerance":
                    distance <= TOLERANCE_YEARS,
            }
        )

    results = pd.DataFrame(results)

    strict = int(
        results["detected_strict"].sum()
    )

    tolerance = int(
        results["detected_tolerance"].sum()
    )

    total = len(results)

    strict_recall = (
        strict / total
        if total
        else 0
    )

    tolerance_recall = (
        tolerance / total
        if total
        else 0
    )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    results.to_csv(
        OUTPUT,
        index=False,
    )

    print()
    print("=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)

    print(
        f"Events evaluated:        {total}"
    )

    print(
        f"Strict detections:       {strict}"
    )

    print(
        f"Strict recall:           {strict_recall:.3f}"
    )

    print(
        f"Within {TOLERANCE_YEARS} years:     {tolerance}"
    )

    print(
        f"Tolerance recall:        {tolerance_recall:.3f}"
    )

    print()
    print("EVENT RESULTS")
    print()

    print(
        results.to_string(
            index=False
        )
    )

    print()
    print(
        f"[OK] Output: {OUTPUT}"
    )

    print()
    print("=" * 80)
    print("GROUND-TRUTH VALIDATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()