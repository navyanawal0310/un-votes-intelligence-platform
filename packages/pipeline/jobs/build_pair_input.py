from __future__ import annotations

from pathlib import Path

from packages.analytics.gold_adapter import (
    load_gold_votes,
    prepare_pair_votes,
)


BASE_DIR = Path(__file__).resolve().parents[3]

GOLD_SOURCE = (
    BASE_DIR
    / "data"
    / "gold"
    / "country_pairs"
    / "country_pair_input.parquet"
)

PAIR_OUTPUT = (
    BASE_DIR
    / "data"
    / "gold"
    / "country_pairs"
    / "country_pair_observations.parquet"
)


def main() -> None:

    print("=" * 70)
    print("UN VOTES ANALYZER — GOLD PAIR BUILD")
    print("=" * 70)

    print()
    print("Loading Gold dataset...")

    df = load_gold_votes(
        GOLD_SOURCE
    )

    print(
        f"[OK] Gold rows: {len(df):,}"
    )

    print()
    print("Building country-pair observations...")

    pair_df = prepare_pair_votes(
        df
    )

    if pair_df.empty:
        raise RuntimeError(
            "No country-pair observations were produced."
        )

    PAIR_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    pair_df.to_parquet(
        PAIR_OUTPUT,
        index=False,
    )

    print(
        f"[OK] Pair observations: "
        f"{len(pair_df):,}"
    )

    print()
    print("Pairs:")

    for pair in sorted(
        pair_df["pair"].unique()
    ):
        count = (
            pair_df["pair"]
            .eq(pair)
            .sum()
        )

        print(
            f"  {pair}: {count:,}"
        )

    print()
    print(
        f"[OK] Written: {PAIR_OUTPUT}"
    )

    print()
    print("=" * 70)
    print("GOLD PAIR BUILD COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()