from __future__ import annotations

import pandas as pd

from packages.warehouse.database import get_connection
from packages.analytics.issue_positions import issue_positions
from packages.analytics.change_points import detect_change_points


COUNTRIES = [
    "IND",
    "CHN",
    "USA",
    "RUS",
]

ISSUES = [
    "NUCLEAR DISARMAMENT",
    "NUCLEAR NON-PROLIFERATION",
    "HUMAN RIGHTS",
    "DISARMAMENT",
]


def main() -> None:

    con = get_connection()

    try:

        print("=" * 80)
        print("REAL-DATA CHANGE-POINT VALIDATION")
        print("=" * 80)

        all_changes = []

        for country in COUNTRIES:

            # Get all issue positions for this country once.
            country_positions = issue_positions(
                con,
                country_code=country,
                min_events=3,
            )

            for issue in ISSUES:

                print()
                print("-" * 80)
                print(f"{country} — {issue}")
                print("-" * 80)

                positions = country_positions[
                    country_positions["issue"].astype(str).str.upper()
                    == issue.upper()
                ].copy()

                if positions.empty:
                    print("No data")
                    continue

                positions = positions.sort_values("year")

                print(
                    f"Observations: {len(positions)} "
                    f"({positions['year'].min()}–{positions['year'].max()})"
                )

                if len(positions) < 10:
                    print(
                        f"Skipped: only {len(positions)} observations"
                    )
                    continue

                changes = detect_change_points(
                    positions,
                    value_column="position_score",
                    year_column="year",
                    country_column="country_code",
                    issue_column="issue",
                    before_window=3,
                    after_window=3,
                    magnitude_threshold=10.0,
                    effect_threshold=0.8,
                    persistence_window=3,
                    min_separation=3,
                )

                if changes.empty:
                    print("No change points detected")
                    continue

                changes["country"] = country
                changes["issue_name"] = issue

                all_changes.append(changes)

                print()
                print("Detected change points:")

                print(
                    changes[
                        [
                            "change_year",
                            "mean_before",
                            "mean_after",
                            "change_magnitude",
                            "effect_size",
                            "persistence",
                            "confirmed",
                            "confidence",
                        ]
                    ].to_string(index=False)
                )

        print()
        print("=" * 80)
        print("CHANGE-POINT SUMMARY")
        print("=" * 80)

        if not all_changes:
            print("No change points detected.")
            return

        result = pd.concat(
            all_changes,
            ignore_index=True,
        )

        result = result.sort_values(
            [
                "confirmed",
                "confidence",
                "change_magnitude",
            ],
            ascending=False,
        )

        print(
            result[
                [
                    "country",
                    "issue_name",
                    "change_year",
                    "change_magnitude",
                    "effect_size",
                    "persistence",
                    "confirmed",
                    "confidence",
                ]
            ]
            .head(25)
            .to_string(index=False)
        )

        print()

        total = len(result)
        confirmed = int(result["confirmed"].sum())

        print(f"Total detected: {total:,}")
        print(f"Confirmed:      {confirmed:,}")

        if total > 0:

            confirmation_rate = (
                result["confirmed"].mean() * 100
            )

            mean_confidence = (
                result["confidence"].mean()
            )

            print(
                f"Confirmation rate: {confirmation_rate:.2f}%"
            )

            print(
                f"Mean confidence:   {mean_confidence:.3f}"
            )

        print()
        print("=" * 80)
        print("REAL-DATA CHANGE-POINT TEST COMPLETE")
        print("=" * 80)

    finally:
        con.close()


if __name__ == "__main__":
    main()