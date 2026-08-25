"""
Build Gold country-pair relationship state artifact.
"""

from pathlib import Path

import pandas as pd

from packages.analytics.relationship_state import build_relationship_state


BASE = Path("data/gold/analytical")

ALIGNMENT_PATH = BASE / "country_pair_alignment.parquet"
EPISODES_PATH = BASE / "country_pair_change_episodes.parquet"
OUTPUT_PATH = BASE / "country_pair_relationships.parquet"


def main() -> None:
    print("=" * 70)
    print("UN VOTES ANALYZER — RELATIONSHIP STATE BUILD")
    print("=" * 70)

    print("\nLoading country-pair alignment...")
    alignment = pd.read_parquet(ALIGNMENT_PATH)
    print(f"[OK] Alignment rows: {len(alignment):,}")

    print("\nLoading change episodes...")
    episodes = pd.read_parquet(EPISODES_PATH)
    print(f"[OK] Episodes: {len(episodes):,}")

    print("\nBuilding relationship states...")

    relationships = build_relationship_state(
        alignment,
        episodes,
    )

    relationships.to_parquet(
        OUTPUT_PATH,
        index=False,
    )

    print(
        f"[OK] Relationship rows: "
        f"{len(relationships):,}"
    )

    pair_count = relationships[
        ["country_a", "country_b"]
    ].drop_duplicates().shape[0]

    country_count = len(
        set(relationships["country_a"])
        | set(relationships["country_b"])
    )

    print(
        f"[OK] Country pairs: {pair_count:,}"
    )

    print(
        f"[OK] Countries: {country_count:,}"
    )

    print("\nRelationship directions:")
    print(
        relationships["relationship_direction"]
        .value_counts()
        .to_string()
    )
    print(f"\n[OK] Output: {OUTPUT_PATH}")

    print("\n" + "=" * 70)
    print("RELATIONSHIP STATE BUILD COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()