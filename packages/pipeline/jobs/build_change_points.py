from __future__ import annotations

from pathlib import Path

import pandas as pd

from packages.analytics.change_points import (
    detect_pair_change_points,
)


BASE_DIR = Path(__file__).resolve().parents[3]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "gold"
    / "analytical"
    / "country_pair_temporal_alignment.parquet"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "gold"
    / "analytical"
    / "country_pair_change_points.parquet"
)


def main() -> None:

    print("=" * 70)
    print("UN VOTES ANALYZER — PAIR CHANGE-POINT BUILD")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input not found: {INPUT_FILE}"
        )

    print("\nLoading temporal alignment...")

    df = pd.read_parquet(INPUT_FILE)

    print(
        f"[OK] Temporal rows: {len(df):,}"
    )

    print("\nDetecting structural changes...")

    changes = detect_pair_change_points(
        df,
        before_window=3,
        after_window=3,
        magnitude_threshold=0.10,
        effect_threshold=0.80,
        persistence_window=3,
    )

    if changes.empty:
        raise RuntimeError(
            "No change-point candidates detected."
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    changes.to_parquet(
        OUTPUT_FILE,
        index=False,
    )

    confirmed = changes[
        changes["confirmed"]
    ]

    print()
    print(
        f"[OK] Candidates: {len(changes):,}"
    )

    print(
        f"[OK] Confirmed: {len(confirmed):,}"
    )

    print(
        f"[OK] Country pairs represented: "
        f"{changes[['country_a', 'country_b']].drop_duplicates().shape[0]:,}"
    )

    print(
        f"[OK] Output: {OUTPUT_FILE}"
    )

    print("\nTOP CONFIRMED CHANGES")

    print(
        confirmed.head(20)
        .to_string(index=False)
    )

    print()
    print("=" * 70)
    print("CHANGE-POINT BUILD COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()