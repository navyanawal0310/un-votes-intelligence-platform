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

MIN_OBSERVATIONS = 10


def main() -> None:

    con = get_connection()

    try:

        print("=" * 90)
        print("ALL-ISSUE REAL-DATA CHANGE-POINT VALIDATION")
        print("=" * 90)

        all_changes = []

        total_series = 0
        eligible_series = 0

        for country in COUNTRIES:

            print()
            print("-" * 90)
            print(f"COUNTRY: {country}")
            print("-" * 90)

            positions = issue_positions(
                con,
                country_code=country,
                min_events=3,
            )
            # Normalize issue_positions schema for the change-point detector.

            if positions.empty:
                print("No issue-position data")
                continue

            positions["issue"] = (
                positions["issue"]
                .astype(str)
                .str.strip()
            )

            positions["year"] = pd.to_numeric(
                positions["year"],
                errors="coerce",
            )

            positions["position_score"] = pd.to_numeric(
                positions["position_score"],
                errors="coerce",
            )

            positions = positions.dropna(
                subset=["country_code","issue", "year", "position_score"]
            )

            issues = sorted(
                positions["issue"].unique()
            )

            print(f"Issues available: {len(issues)}")

            for issue in issues:

                series = positions[
                    positions["issue"] == issue
                ].copy()

                series = (
                    series
                    .sort_values("year")
                    .drop_duplicates(
                        subset=["year"],
                        keep="last",
                    )
                )

                total_series += 1

                if len(series) < MIN_OBSERVATIONS:
                    continue

                eligible_series += 1

                try:

                    changes = detect_change_points(
                        series,
                        before_window=3,
                        after_window=3,
                        magnitude_threshold=0.40,
                        effect_threshold=0.50,
                        persistence_window=3,
                    )

                except Exception as exc:

                    print(
                        f"WARNING: {issue}: "
                        f"{type(exc).__name__}: {exc}"
                    )

                    continue

                if changes.empty:
                    continue

                changes = changes.copy()

                changes["country"] = country
                changes["issue"] = issue
                changes["observations"] = len(series)
                changes["first_year"] = int(series["year"].min())
                changes["last_year"] = int(series["year"].max())

                all_changes.append(changes)

        print()
        print("=" * 90)
        print("CHANGE-POINT VALIDATION SUMMARY")
        print("=" * 90)

        print()
        print(f"Total country × issue series: {total_series:,}")
        print(
            f"Eligible series (>={MIN_OBSERVATIONS} observations): "
            f"{eligible_series:,}"
        )

        if total_series:
            coverage = (
                eligible_series / total_series * 100
            )
        else:
            coverage = 0.0

        print(
            f"Temporal coverage rate: {coverage:.2f}%"
        )

        if not all_changes:

            print()
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
                "effect_size",
                "change_magnitude",
            ],
            ascending=False,
        )

        print()
        print("TOP DETECTED CHANGE POINTS")
        print("-" * 90)

        display_columns = [
            "country",
            "issue",
            "change_year",
            "change_magnitude",
            "effect_size",
            "persistence",
            "confirmed",
            "confidence",
            "observations",
        ]

        print(
            result[
                display_columns
            ].head(30).to_string(index=False)
        )

        print()
        print("-" * 90)

        print(
            f"Candidate change points: {len(result):,}"
        )

        confirmed = int(
            result["confirmed"].sum()
        )

        print(
            f"Confirmed by detector rules: {confirmed:,}"
        )

        confirmation_rate = (
            confirmed / len(result) * 100
        )

        print(
            f"Confirmation rate: {confirmation_rate:.2f}%"
        )

        print(
            f"Mean confidence: "
            f"{result['confidence'].mean():.3f}"
        )

        print(
            f"Median confidence: "
            f"{result['confidence'].median():.3f}"
        )

        print(
            f"Mean effect size: "
            f"{result['effect_size'].mean():.3f}"
        )

        print(
            f"Median effect size: "
            f"{result['effect_size'].median():.3f}"
        )

        print()
        print("CHANGE POINTS BY COUNTRY")
        print("-" * 90)

        by_country = (
            result
            .groupby("country")
            .agg(
                change_points=("change_year", "count"),
                confirmed=("confirmed", "sum"),
                mean_confidence=("confidence", "mean"),
            )
            .reset_index()
        )

        print(
            by_country.to_string(index=False)
        )

        print()
        print("CHANGE POINTS BY ISSUE")
        print("-" * 90)

        by_issue = (
            result
            .groupby("issue")
            .agg(
                change_points=("change_year", "count"),
                confirmed=("confirmed", "sum"),
                mean_confidence=("confidence", "mean"),
            )
            .sort_values(
                "change_points",
                ascending=False,
            )
            .reset_index()
        )

        print(
            by_issue.head(25).to_string(index=False)
        )

        # Save for subsequent ground-truth evaluation.
        output_path = (
            "change_point_candidates.csv"
        )

        result.to_csv(
            output_path,
            index=False,
        )

        print()
        print(
            f"Saved candidate events to: "
            f"{output_path}"
        )

        print()
        print("=" * 90)
        print(
            "ALL-ISSUE CHANGE-POINT TEST COMPLETE"
        )
        print("=" * 90)

    finally:

        con.close()


if __name__ == "__main__":
    main()