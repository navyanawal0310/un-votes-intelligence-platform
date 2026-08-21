from __future__ import annotations

import pandas as pd

from packages.analytics.temporal_change_episodes import (
    build_change_episodes,
)


def main():

    input_path = "temporal_alignment_change_points.csv"

    changes = pd.read_csv(input_path)

    episodes = build_change_episodes(
        changes,
        max_gap=2,
    )

    print("=" * 90)
    print("TEMPORAL CHANGE EPISODE ANALYSIS")
    print("=" * 90)

    if episodes.empty:

        print("No change episodes detected.")

        return

    print()
    print(
        episodes.to_string(
            index=False
        )
    )

    output_path = (
        "temporal_alignment_change_episodes.csv"
    )

    episodes.to_csv(
        output_path,
        index=False,
    )

    print()
    print(
        f"Total episodes: {len(episodes)}"
    )

    print(
        f"Saved: {output_path}"
    )

    print()
    print("=" * 90)
    print("TEMPORAL EPISODE ANALYSIS COMPLETE")
    print("=" * 90)


if __name__ == "__main__":
    main()