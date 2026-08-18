import pandas as pd
from packages.warehouse.database import get_connection
from packages.analytics.country_alignment import country_alignment


def main():

    con = get_connection()

    try:

        pairs = [
            ("IND", "CHN"),
            ("IND", "USA"),
            ("IND", "RUS"),
            ("CHN", "USA"),
            ("CHN", "RUS"),
            ("USA", "RUS"),
        ]

        all_results = []

        for country_a, country_b in pairs:

            result = country_alignment(
                con,
                country_a,
                country_b,
                min_events=3,
            )

            if result.empty:
                print(
                    f"{country_a}-{country_b}: "
                    "no common observations"
                )
                continue

            result.to_csv(
                f"alignment_{country_a}_{country_b}.csv",
                index=False,
            )

            print()
            print("=" * 80)
            print(
                f"{country_a} vs {country_b}"
            )
            print("=" * 80)

            print(
                f"Common issue-year observations: "
                f"{len(result)}"
            )

            print(
                f"Mean alignment: "
                f"{result['alignment_score'].mean():.3f}"
            )

            print(
                f"Median alignment: "
                f"{result['alignment_score'].median():.3f}"
            )

            print(
                f"Mean divergence: "
                f"{result['absolute_divergence'].mean():.3f}"
            )

            print(
                f"Directional agreement: "
                f"{result['directional_agreement'].mean():.3f}"
            )

            all_results.append(result)

        if all_results:

            combined = pd.concat(
                all_results,
                ignore_index=True,
            )

            summary = (
                combined
                .groupby(
                    [
                        "country_a",
                        "country_b",
                    ]
                )
                .agg(
                    observations=(
                        "alignment_score",
                        "count",
                    ),
                    mean_alignment=(
                        "alignment_score",
                        "mean",
                    ),
                    median_alignment=(
                        "alignment_score",
                        "median",
                    ),
                    mean_divergence=(
                        "absolute_divergence",
                        "mean",
                    ),
                    directional_agreement=(
                        "directional_agreement",
                        "mean",
                    ),
                )
                .reset_index()
            )

            summary = summary.sort_values(
                "mean_alignment",
                ascending=False,
            )

            print()
            print("=" * 80)
            print("COUNTRY PAIR ALIGNMENT SUMMARY")
            print("=" * 80)

            print(
                summary.round(3).to_string(
                    index=False
                )
            )

            summary.to_csv(
                "country_pair_alignment_summary.csv",
                index=False,
            )

            combined.to_csv(
                "country_pair_alignment.csv",
                index=False,
            )

            print()
            print(
                "Saved country_pair_alignment.csv"
            )

            print(
                "Saved country_pair_alignment_summary.csv"
            )

    finally:

        con.close()


if __name__ == "__main__":
    main()