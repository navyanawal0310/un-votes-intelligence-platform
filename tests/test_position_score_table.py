from __future__ import annotations

import pandas as pd

from packages.warehouse.database import get_connection
from packages.analytics.issue_positions import issue_positions


COUNTRIES = ["IND", "CHN", "USA", "RUS"]


def main():

    con = get_connection()

    try:

        print("=" * 80)
        print("POSITION SCORE SCALE AUDIT")
        print("=" * 80)

        all_data = []

        for country in COUNTRIES:

            df = issue_positions(
                con,
                country_code=country,
                min_events=3,
            )

            if df.empty:
                continue

            print()
            print("-" * 80)
            print(f"COUNTRY: {country}")
            print("-" * 80)

            print("Rows:", len(df))

            print(
                "Position score min:",
                df["position_score"].min()
            )

            print(
                "Position score max:",
                df["position_score"].max()
            )

            print(
                "Position score mean:",
                round(
                    df["position_score"].mean(),
                    4
                )
            )

            print(
                "Position score std:",
                round(
                    df["position_score"].std(),
                    4
                )
            )

            print()
            print("Unique position scores:")

            print(
                sorted(
                    df["position_score"]
                    .dropna()
                    .unique()
                    .tolist()
                )
            )

            print()
            print("Score frequency:")

            print(
                df["position_score"]
                .value_counts()
                .sort_index()
                .to_string()
            )

            all_data.append(df)

        if not all_data:
            print("No data available.")
            return

        combined = pd.concat(
            all_data,
            ignore_index=True
        )

        print()
        print("=" * 80)
        print("GLOBAL POSITION SCORE SCALE")
        print("=" * 80)

        print(
            "Rows:",
            len(combined)
        )

        print(
            "Minimum:",
            combined["position_score"].min()
        )

        print(
            "Maximum:",
            combined["position_score"].max()
        )

        print(
            "Mean:",
            round(
                combined["position_score"].mean(),
                4
            )
        )

        print(
            "Std:",
            round(
                combined["position_score"].std(),
                4
            )
        )

        print()
        print("Unique values:")

        print(
            sorted(
                combined["position_score"]
                .dropna()
                .unique()
                .tolist()
            )
        )

        print()
        print("=" * 80)
        print("POSITION SCORE AUDIT COMPLETE")
        print("=" * 80)

    finally:

        con.close()


if __name__ == "__main__":
    main()