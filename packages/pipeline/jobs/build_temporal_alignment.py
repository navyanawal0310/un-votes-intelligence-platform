from __future__ import annotations

from pathlib import Path

import pandas as pd

from packages.analytics.temporal_alignment import (
    temporal_alignment,
)


BASE_DIR = Path(__file__).resolve().parents[3]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "gold"
    / "analytical"
    / "country_pair_alignment.parquet"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "gold"
    / "analytical"
    / "country_pair_temporal_alignment.parquet"
)


def main() -> None:

    print("=" * 70)
    print("UN VOTES ANALYZER — TEMPORAL ALIGNMENT")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input not found: {INPUT_FILE}"
        )

    print()
    print("Loading annual alignment...")

    alignment = pd.read_parquet(
        INPUT_FILE
    )

    print(
        f"[OK] Alignment rows: "
        f"{len(alignment):,}"
    )

    print()
    print(
        "Calculating rolling temporal alignment..."
    )

    temporal = temporal_alignment(
        alignment,
        window=5,
        min_observations=3,
    )

    if temporal.empty:
        raise RuntimeError(
            "Temporal alignment produced no results."
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporal.to_parquet(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print(
        f"[OK] Temporal rows: "
        f"{len(temporal):,}"
    )

    print(
        f"[OK] Country pairs: "
        f"{temporal['country_a'].astype(str).str.cat(temporal['country_b'].astype(str), sep='-').nunique():,}"
    )

    print(
        f"[OK] Output: {OUTPUT_FILE}"
    )

    print()
    print("SAMPLE")
    print(
        temporal.head(10)
        .to_string(index=False)
    )

    print()
    print("=" * 70)
    print("TEMPORAL ALIGNMENT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()