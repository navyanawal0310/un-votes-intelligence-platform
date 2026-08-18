import pandas as pd

from packages.analytics.temporal_alignment import (
    temporal_alignment,
)


def main():

    df = pd.read_csv(
        "country_pair_alignment.csv"
    )

    result = temporal_alignment(
        df,
        window=5,
        min_observations=3,
    )

    print("=" * 90)
    print("5-YEAR TEMPORAL COUNTRY ALIGNMENT")
    print("=" * 90)

    print()

    for country_a, country_b in [
        ("IND", "CHN"),
        ("IND", "RUS"),
        ("IND", "USA"),
    ]:

        subset = result[
            (result["country_a"] == country_a)
            &
            (result["country_b"] == country_b)
        ]

        print()
        print(
            f"{country_a}–{country_b}"
        )
        print("-" * 90)

        print(
            subset[
                [
                    "window_start",
                    "window_end",
                    "observations",
                    "mean_alignment",
                    "mean_divergence",
                    "directional_agreement",
                ]
            ]
            .round(3)
            .to_string(index=False)
        )

    result.to_csv(
        "country_pair_temporal_alignment.csv",
        index=False,
    )

    print()
    print(
        "Saved country_pair_temporal_alignment.csv"
    )


if __name__ == "__main__":
    main()