from __future__ import annotations

import pandas as pd

from packages.analytics.temporal_change_points import (
    detect_temporal_alignment_changes,
)


PAIRS = [
    ("IND", "CHN"),
    ("IND", "RUS"),
    ("IND", "USA"),
]


def main():

    df = pd.read_csv(
        "country_pair_temporal_alignment.csv"
    )

    print("=" * 90)
    print("TEMPORAL ALIGNMENT CHANGE-POINT ANALYSIS")
    print("=" * 90)

    all_results = []

    for country_a, country_b in PAIRS:

        pair = df[
            (df["country_a"] == country_a)
            &
            (df["country_b"] == country_b)
        ].copy()

        if pair.empty:
            continue

        print()
        print(
            f"{country_a}–{country_b}"
        )
        print("-" * 90)

        changes = detect_temporal_alignment_changes(
            pair,
            before_window=3,
            after_window=3,
            magnitude_threshold=0.10,
            effect_threshold=0.80,
            persistence_window=2,
        )

        if changes.empty:

            print("No temporal change points detected.")
            continue

        changes = changes.copy()

        changes["country_a"] = country_a
        changes["country_b"] = country_b

        all_results.append(changes)

        print(
            changes[
                [
                    "change_year",
                    "change_magnitude",
                    "effect_size",
                    "persistence",
                    "confirmed",
                    "confidence",
                ]
            ]
            .round(3)
            .to_string(index=False)
        )

    if not all_results:

        print()
        print("No temporal change points detected.")
        return

    result = pd.concat(
        all_results,
        ignore_index=True,
    )

    result.to_csv(
        "temporal_alignment_change_points.csv",
        index=False,
    )

    print()
    print("=" * 90)
    print("TEMPORAL CHANGE-POINT SUMMARY")
    print("=" * 90)

    print(
        result[
            [
                "country_a",
                "country_b",
                "change_year",
                "change_magnitude",
                "effect_size",
                "confirmed",
                "confidence",
            ]
        ]
        .sort_values(
            "confidence",
            ascending=False,
        )
        .round(3)
        .to_string(index=False)
    )

    print()
    print(
        "Saved: temporal_alignment_change_points.csv"
    )


if __name__ == "__main__":
    main()