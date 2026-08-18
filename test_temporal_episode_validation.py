from __future__ import annotations

import pandas as pd


EPISODES_PATH = (
    "temporal_alignment_change_episodes.csv"
)

TEMPORAL_ALIGNMENT_PATH = (
    "country_pair_temporal_alignment.csv"
)

PRE_WINDOW = 3
POST_WINDOW = 3


def load_temporal_alignment() -> pd.DataFrame:

    df = pd.read_csv(
        TEMPORAL_ALIGNMENT_PATH
    )

    required = [
        "country_a",
        "country_b",
        "window_start",
        "window_end",
        "mean_alignment",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing required columns: "
            f"{missing}"
        )

    df["window_start"] = pd.to_numeric(
        df["window_start"],
        errors="coerce",
    )

    df["window_end"] = pd.to_numeric(
        df["window_end"],
        errors="coerce",
    )

    df["mean_alignment"] = pd.to_numeric(
        df["mean_alignment"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "country_a",
            "country_b",
            "window_end",
            "mean_alignment",
        ]
    )

    df["window_start"] = (
        df["window_start"].astype(int)
    )

    df["window_end"] = (
        df["window_end"].astype(int)
    )

    return df.sort_values(
        [
            "country_a",
            "country_b",
            "window_end",
        ]
    )


def validate_episode(
    alignment: pd.DataFrame,
    episode: pd.Series,
):

    country_a = episode["country_a"]
    country_b = episode["country_b"]

    start = int(
        episode["episode_start"]
    )

    end = int(
        episode["episode_end"]
    )

    series = alignment[
        (alignment["country_a"] == country_a)
        &
        (alignment["country_b"] == country_b)
    ].copy()

    if series.empty:
        return None

    series = series.sort_values(
        "window_end"
    )

    # Use the same temporal coordinate used
    # by the change-point detector.
    pre = series[
        (series["window_end"] < start)
        &
        (
            series["window_end"]
            >= start - PRE_WINDOW
        )
    ]

    post = series[
        (series["window_end"] > end)
        &
        (
            series["window_end"]
            <= end + POST_WINDOW
        )
    ]

    if pre.empty or post.empty:
        return None

    pre_mean = (
        pre["mean_alignment"].mean()
    )

    post_mean = (
        post["mean_alignment"].mean()
    )

    absolute_shift = abs(
        post_mean - pre_mean
    )

    if abs(pre_mean) > 1e-12:

        relative_shift = (
            absolute_shift
            / abs(pre_mean)
        )

    else:

        relative_shift = None

    return {
        "country_a": country_a,
        "country_b": country_b,

        "episode_start": start,
        "episode_end": end,

        "peak_change_year": int(
            episode["peak_change_year"]
        ),

        "pre_observations": len(pre),
        "post_observations": len(post),

        "pre_mean_alignment": round(
            pre_mean,
            6,
        ),

        "post_mean_alignment": round(
            post_mean,
            6,
        ),

        "absolute_shift": round(
            absolute_shift,
            6,
        ),

        "relative_shift": (
            round(
                relative_shift,
                6,
            )
            if relative_shift is not None
            else None
        ),

        "max_change_magnitude": round(
            float(
                episode[
                    "max_change_magnitude"
                ]
            ),
            6,
        ),

        "max_effect_size": round(
            float(
                episode[
                    "max_effect_size"
                ]
            ),
            6,
        ),

        "max_confidence": round(
            float(
                episode[
                    "max_confidence"
                ]
            ),
            6,
        ),

        "detections": int(
            episode["detections"]
        ),

        "confirmed_detections": int(
            episode[
                "confirmed_detections"
            ]
        ),
    }


def main():

    print("=" * 90)
    print(
        "TEMPORAL CHANGE EPISODE VALIDATION"
    )
    print("=" * 90)

    episodes = pd.read_csv(
        EPISODES_PATH
    )

    print()
    print(
        f"Detected episodes: "
        f"{len(episodes)}"
    )

    alignment = load_temporal_alignment()

    print(
        "Temporal alignment observations: "
        f"{len(alignment):,}"
    )

    print(
        "Country pairs: "
        f"{alignment[['country_a', 'country_b']].drop_duplicates().shape[0]}"
    )

    results = []

    for _, episode in episodes.iterrows():

        result = validate_episode(
            alignment,
            episode,
        )

        if result is None:

            print()
            print(
                "WARNING: insufficient pre/post "
                "observations for "
                f"{episode['country_a']}-"
                f"{episode['country_b']} "
                f"{episode['episode_start']}-"
                f"{episode['episode_end']}"
            )

            continue

        results.append(result)

    print()
    print("=" * 90)
    print(
        "EPISODE VALIDATION RESULTS"
    )
    print("=" * 90)

    if not results:

        print()
        print(
            "No episodes could be validated."
        )

        return

    result = pd.DataFrame(
        results
    )

    columns = [
        "country_a",
        "country_b",
        "episode_start",
        "episode_end",
        "peak_change_year",
        "pre_observations",
        "post_observations",
        "pre_mean_alignment",
        "post_mean_alignment",
        "absolute_shift",
        "relative_shift",
        "max_change_magnitude",
        "max_effect_size",
        "max_confidence",
        "detections",
        "confirmed_detections",
    ]

    print()
    print(
        result[
            columns
        ].to_string(index=False)
    )

    print()
    print("=" * 90)
    print(
        "VALIDATION SUMMARY"
    )
    print("=" * 90)

    print()
    print(
        f"Episodes evaluated: "
        f"{len(result)}"
    )

    print(
        "Mean absolute alignment shift: "
        f"{result['absolute_shift'].mean():.4f}"
    )

    print(
        "Median absolute alignment shift: "
        f"{result['absolute_shift'].median():.4f}"
    )

    print(
        "Maximum absolute alignment shift: "
        f"{result['absolute_shift'].max():.4f}"
    )

    print(
        "Episodes with shift >= 0.10: "
        f"{(result['absolute_shift'] >= 0.10).sum()}"
    )

    print(
        "Episodes with shift >= 0.20: "
        f"{(result['absolute_shift'] >= 0.20).sum()}"
    )

    output_path = (
        "temporal_alignment_episode_validation.csv"
    )

    result.to_csv(
        output_path,
        index=False,
    )

    print()
    print(
        "Saved validation results to: "
        f"{output_path}"
    )

    print()
    print("=" * 90)
    print(
        "TEMPORAL EPISODE VALIDATION COMPLETE"
    )
    print("=" * 90)


if __name__ == "__main__":
    main()