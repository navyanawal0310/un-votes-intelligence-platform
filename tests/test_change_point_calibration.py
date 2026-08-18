from __future__ import annotations

import inspect
import numpy as np
import pandas as pd

from packages.warehouse.database import get_connection
from packages.analytics.issue_positions import issue_positions
from packages.analytics.change_points import detect_change_points


COUNTRIES = ["IND", "CHN", "USA", "RUS"]
MIN_OBSERVATIONS = 10


def main() -> None:

    con = get_connection()

    try:

        print("=" * 90)
        print("CHANGE-POINT DETECTOR CALIBRATION")
        print("=" * 90)

        print()
        print("DETECTOR API")
        print("-" * 90)
        print(inspect.signature(detect_change_points))

        diagnostics = []

        for country in COUNTRIES:

            positions = issue_positions(
                con,
                country_code=country,
                min_events=3,
            )

            if positions.empty:
                continue

            positions = positions.rename(
                columns={
                    "country_code": "ms_code",
                    "issue": "subject",
                }
            )

            positions["subject"] = (
                positions["subject"]
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
                subset=[
                    "subject",
                    "year",
                    "position_score",
                ]
            )

            for issue in sorted(
                positions["subject"].unique()
            ):

                series = positions[
                    positions["subject"] == issue
                ].copy()

                series = (
                    series
                    .sort_values("year")
                    .drop_duplicates(
                        subset=["year"],
                        keep="last",
                    )
                )

                if len(series) < MIN_OBSERVATIONS:
                    continue

                values = series[
                    "position_score"
                ].to_numpy(dtype=float)

                years = series[
                    "year"
                ].to_numpy(dtype=int)

                changes = np.abs(
                    np.diff(values)
                )

                if len(changes) == 0:
                    continue

                max_change_idx = int(
                    np.argmax(changes)
                )

                diagnostics.append(
                    {
                        "country": country,
                        "issue": issue,
                        "observations": len(values),
                        "first_year": years[0],
                        "last_year": years[-1],
                        "min_position": np.min(values),
                        "max_position": np.max(values),
                        "range": np.max(values) - np.min(values),
                        "mean_position": np.mean(values),
                        "std_position": np.std(values),
                        "max_year_to_year_change": changes[
                            max_change_idx
                        ],
                        "largest_change_year": years[
                            max_change_idx + 1
                        ],
                    }
                )

        if not diagnostics:

            print()
            print("No eligible series.")
            return

        df = pd.DataFrame(diagnostics)

        print()
        print("=" * 90)
        print("SERIES DIAGNOSTICS")
        print("=" * 90)

        print(
            f"Eligible country × issue series: {len(df):,}"
        )

        print()
        print(
            "Position-score range across eligible series:"
        )

        print(
            f"Minimum: {df['min_position'].min():.3f}"
        )

        print(
            f"Maximum: {df['max_position'].max():.3f}"
        )

        print(
            f"Median series range: "
            f"{df['range'].median():.3f}"
        )

        print(
            f"Maximum series range: "
            f"{df['range'].max():.3f}"
        )

        print()
        print(
            f"Median largest year-to-year change: "
            f"{df['max_year_to_year_change'].median():.3f}"
        )

        print(
            f"Maximum year-to-year change: "
            f"{df['max_year_to_year_change'].max():.3f}"
        )

        print()
        print("=" * 90)
        print("LARGEST OBSERVED CHANGES")
        print("=" * 90)

        print(
            df.sort_values(
                "max_year_to_year_change",
                ascending=False,
            )[
                [
                    "country",
                    "issue",
                    "observations",
                    "largest_change_year",
                    "max_year_to_year_change",
                    "range",
                ]
            ]
            .head(30)
            .to_string(index=False)
        )

        print()
        print("=" * 90)
        print("THRESHOLD COVERAGE")
        print("=" * 90)

        for threshold in [
            5,
            10,
            15,
            20,
            25,
            30,
            40,
            50,
        ]:

            count = int(
                (
                    df["max_year_to_year_change"]
                    >= threshold
                ).sum()
            )

            percentage = (
                count / len(df) * 100
            )

            print(
                f"Threshold >= {threshold:>2}: "
                f"{count:>3} series "
                f"({percentage:>6.2f}%)"
            )

        print()
        print("=" * 90)
        print("CALIBRATION COMPLETE")
        print("=" * 90)

    finally:

        con.close()


if __name__ == "__main__":
    main()