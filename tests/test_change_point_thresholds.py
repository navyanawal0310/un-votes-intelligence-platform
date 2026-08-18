from __future__ import annotations

import pandas as pd

from packages.warehouse.database import get_connection
from packages.analytics.issue_positions import issue_positions
from packages.analytics.change_points import detect_change_points


COUNTRIES = ["IND", "CHN", "USA", "RUS"]

MIN_OBSERVATIONS = 10

MAGNITUDE_THRESHOLDS = [
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
    0.40,
]

EFFECT_THRESHOLDS = [
    0.30,
    0.50,
    0.80,
    1.00,
]


def load_series(con):

    series_list = []

    for country in COUNTRIES:

        positions = issue_positions(
            con,
            country_code=country,
            min_events=3,
        )

        if positions.empty:
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
            subset=[
                "issue",
                "year",
                "position_score",
            ]
        )

        for issue in sorted(
            positions["issue"].unique()
        ):

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

            if len(series) < MIN_OBSERVATIONS:
                continue

            series_list.append(
                {
                    "country": country,
                    "issue": issue,
                    "data": series,
                }
            )

    return series_list


def main():

    con = get_connection()

    try:

        print("=" * 90)
        print("CHANGE-POINT THRESHOLD CALIBRATION")
        print("=" * 90)

        series_list = load_series(con)

        print()
        print(
            f"Eligible country × issue series: "
            f"{len(series_list)}"
        )

        results = []

        for magnitude in MAGNITUDE_THRESHOLDS:

            for effect in EFFECT_THRESHOLDS:

                detected = 0
                confirmed = 0

                series_with_changes = 0

                for item in series_list:

                    try:

                        changes = detect_change_points(
                            item["data"],
                            before_window=3,
                            after_window=3,
                            magnitude_threshold=magnitude,
                            effect_threshold=effect,
                            persistence_window=3,
                        )

                    except Exception as exc:

                        print(
                            f"WARNING: "
                            f"{item['country']} / "
                            f"{item['issue']}: "
                            f"{type(exc).__name__}: {exc}"
                        )

                        continue

                    if changes.empty:
                        continue

                    series_with_changes += 1
                    detected += len(changes)

                    if "confirmed" in changes.columns:

                        confirmed += int(
                            changes["confirmed"].sum()
                        )

                results.append(
                    {
                        "magnitude_threshold": magnitude,
                        "effect_threshold": effect,
                        "series_with_changes":
                            series_with_changes,
                        "candidate_events":
                            detected,
                        "confirmed_events":
                            confirmed,
                        "event_rate":
                            (
                                detected
                                / len(series_list)
                                if series_list
                                else 0
                            ),
                    }
                )

        result = pd.DataFrame(results)

        print()
        print("=" * 90)
        print("THRESHOLD SWEEP RESULTS")
        print("=" * 90)

        print(
            result.to_string(
                index=False,
            )
        )

        print()
        print("=" * 90)
        print("RECOMMENDED CALIBRATION CANDIDATES")
        print("=" * 90)

        candidates = result[
            (result["candidate_events"] > 0)
            &
            (result["event_rate"] <= 1.0)
        ].copy()

        if candidates.empty:

            print(
                "No threshold combination produced "
                "detectable events."
            )

        else:

            candidates = candidates.sort_values(
                [
                    "candidate_events",
                    "magnitude_threshold",
                    "effect_threshold",
                ],
                ascending=[
                    True,
                    False,
                    False,
                ],
            )

            print(
                candidates.to_string(
                    index=False,
                )
            )

        output_path = (
            "change_point_threshold_sweep.csv"
        )

        result.to_csv(
            output_path,
            index=False,
        )

        print()
        print(
            f"Saved results to: {output_path}"
        )

        print()
        print("=" * 90)
        print("THRESHOLD CALIBRATION COMPLETE")
        print("=" * 90)

    finally:

        con.close()


if __name__ == "__main__":
    main()