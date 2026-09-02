from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

EPISODE_FILE = BASE_DIR / "temporal_alignment_change_episodes.csv"
OUTPUT_FILE = BASE_DIR / "temporal_issue_episode_attribution.csv"

WINDOW_YEARS = 3
MIN_OBSERVATIONS = 2
TOP_N = 10


# ============================================================
# HELPERS
# ============================================================

def normalize_pair(a, b):
    return f"{str(a).upper()}-{str(b).upper()}"


def get_alignment_file(pair):
    return BASE_DIR / f"alignment_{pair.replace('-', '_')}.csv"


def load_episodes():

    if not EPISODE_FILE.exists():
        raise FileNotFoundError(
            f"Missing episode file:\n{EPISODE_FILE}"
        )

    df = pd.read_csv(EPISODE_FILE)

    required = {
        "country_a",
        "country_b",
        "episode_start",
        "episode_end",
        "peak_change_year",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Episode file missing columns: {sorted(missing)}\n"
            f"Available columns: {list(df.columns)}"
        )

    for col in [
        "episode_start",
        "episode_end",
        "peak_change_year",
    ]:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df = df.dropna(
        subset=[
            "country_a",
            "country_b",
            "peak_change_year",
        ]
    ).copy()

    return df


def load_alignment(pair):

    path = get_alignment_file(pair)

    if not path.exists():
        print(
            f"WARNING: alignment file not found: {path.name}"
        )
        return None

    df = pd.read_csv(path)

    required = {
        "country_a",
        "country_b",
        "issue",
        "year",
        "alignment_score",
    }

    missing = required - set(df.columns)

    if missing:
        print(
            f"WARNING: {path.name} missing columns: "
            f"{sorted(missing)}"
        )
        return None

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce"
    )

    df["alignment_score"] = pd.to_numeric(
        df["alignment_score"],
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            "issue",
            "year",
            "alignment_score",
        ]
    ).copy()

    return df


# ============================================================
# EPISODE-LEVEL ATTRIBUTION
# ============================================================

def calculate_episode_attribution(
    alignment,
    country_a,
    country_b,
    episode_start,
    episode_end,
    peak_year,
):

    results = []

    issues = (
        alignment["issue"]
        .dropna()
        .astype(str)
        .unique()
    )

    for issue in issues:

        issue_df = alignment[
            alignment["issue"].astype(str) == issue
        ].copy()

        # ----------------------------------------------------
        # BEFORE THE EPISODE
        # ----------------------------------------------------

        before = issue_df[
            (
                issue_df["year"]
                >= episode_start - WINDOW_YEARS
            )
            &
            (
                issue_df["year"]
                < episode_start
            )
        ].copy()

        # ----------------------------------------------------
        # DURING THE EPISODE
        # ----------------------------------------------------

        during = issue_df[
            (
                issue_df["year"]
                >= episode_start
            )
            &
            (
                issue_df["year"]
                <= episode_end
            )
        ].copy()

        # ----------------------------------------------------
        # AFTER THE EPISODE
        # ----------------------------------------------------

        after = issue_df[
            (
                issue_df["year"]
                > episode_end
            )
            &
            (
                issue_df["year"]
                <= episode_end + WINDOW_YEARS
            )
        ].copy()

        if len(before) < MIN_OBSERVATIONS:
            continue

        if len(after) < MIN_OBSERVATIONS:
            continue

        before_mean = before[
            "alignment_score"
        ].mean()

        after_mean = after[
            "alignment_score"
        ].mean()

        episode_mean = (
            during["alignment_score"].mean()
            if len(during) > 0
            else np.nan
        )

        # ----------------------------------------------------
        # NET EPISODE SHIFT
        # ----------------------------------------------------

        episode_shift = after_mean - before_mean

        absolute_shift = abs(
            episode_shift
        )

        # ----------------------------------------------------
        # EPISODE DIRECTION
        # ----------------------------------------------------

        if episode_shift > 0:
            direction = "INCREASING"

        elif episode_shift < 0:
            direction = "DECREASING"

        else:
            direction = "STABLE"

        # ----------------------------------------------------
        # PEAK-YEAR LOCAL SHIFT
        # ----------------------------------------------------

        peak_before = issue_df[
            (
                issue_df["year"]
                >= peak_year - 1
            )
            &
            (
                issue_df["year"]
                < peak_year
            )
        ]

        peak_after = issue_df[
            (
                issue_df["year"]
                > peak_year
            )
            &
            (
                issue_df["year"]
                <= peak_year + 1
            )
        ]

        if (
            len(peak_before) > 0
            and len(peak_after) > 0
        ):

            peak_shift = (
                peak_after["alignment_score"].mean()
                -
                peak_before["alignment_score"].mean()
            )

        else:
            peak_shift = np.nan

        results.append({
            "country_a": country_a,
            "country_b": country_b,
            "episode_start": int(episode_start),
            "episode_end": int(episode_end),
            "peak_change_year": int(peak_year),
            "issue": issue,
            "before_observations": len(before),
            "episode_observations": len(during),
            "after_observations": len(after),
            "mean_before": before_mean,
            "mean_episode": episode_mean,
            "mean_after": after_mean,
            "episode_shift": episode_shift,
            "absolute_shift": absolute_shift,
            "peak_local_shift": peak_shift,
            "issue_direction": direction,
        })

    if not results:
        return pd.DataFrame()

    result = pd.DataFrame(results)

    total_shift = result[
        "absolute_shift"
    ].sum()

    if total_shift > 0:

        result[
            "share_of_episode_change"
        ] = (
            result["absolute_shift"]
            / total_shift
        )

    else:

        result[
            "share_of_episode_change"
        ] = 0.0

    result[
        "contribution_percent"
    ] = (
        result["share_of_episode_change"]
        * 100
    )

    result = result.sort_values(
        "absolute_shift",
        ascending=False
    ).reset_index(drop=True)

    result["rank"] = (
        np.arange(len(result)) + 1
    )

    return result


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("TEMPORAL EPISODE-LEVEL ISSUE ATTRIBUTION")
    print("=" * 80)

    episodes = load_episodes()

    print(
        f"\nEpisodes evaluated: {len(episodes)}"
    )

    all_results = []

    for _, episode in episodes.iterrows():

        country_a = str(
            episode["country_a"]
        ).upper()

        country_b = str(
            episode["country_b"]
        ).upper()

        pair = normalize_pair(
            country_a,
            country_b
        )

        episode_start = int(
            episode["episode_start"]
        )

        episode_end = int(
            episode["episode_end"]
        )

        peak_year = int(
            episode["peak_change_year"]
        )

        print("\n" + "=" * 80)

        print(
            f"{pair} | "
            f"Episode {episode_start}-{episode_end} | "
            f"Peak {peak_year}"
        )

        alignment = load_alignment(pair)

        if alignment is None:
            continue

        attribution = calculate_episode_attribution(
            alignment=alignment,
            country_a=country_a,
            country_b=country_b,
            episode_start=episode_start,
            episode_end=episode_end,
            peak_year=peak_year,
        )

        if attribution.empty:

            print(
                "No issues met the observation requirement."
            )

            continue

        all_results.append(
            attribution
        )

        print(
            "\nTOP ISSUES CONTRIBUTING TO EPISODE"
        )

        print(
            attribution[
                [
                    "rank",
                    "issue",
                    "mean_before",
                    "mean_episode",
                    "mean_after",
                    "episode_shift",
                    "contribution_percent",
                    "issue_direction",
                ]
            ]
            .head(TOP_N)
            .to_string(index=False)
        )

    if not all_results:

        print(
            "\nNo episode-level attribution results."
        )

        return

    result = pd.concat(
        all_results,
        ignore_index=True
    )

    # ========================================================
    # RANK WITHIN EACH EPISODE
    # ========================================================

    result = result.sort_values(
        [
            "country_a",
            "country_b",
            "episode_start",
            "episode_end",
            "absolute_shift",
        ],
        ascending=[
            True,
            True,
            True,
            True,
            False,
        ],
    )

    result["rank"] = (
        result
        .groupby(
            [
                "country_a",
                "country_b",
                "episode_start",
                "episode_end",
            ]
        )
        .cumcount()
        + 1
    )

    # ========================================================
    # SAVE
    # ========================================================

    result.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    unique_episodes = (
        result[
            [
                "country_a",
                "country_b",
                "episode_start",
                "episode_end",
            ]
        ]
        .drop_duplicates()
        .shape[0]
    )

    strong_10 = (
        result[
            "contribution_percent"
        ] >= 10
    ).sum()

    strong_20 = (
        result[
            "contribution_percent"
        ] >= 20
    ).sum()

    print("\n")
    print("=" * 80)
    print("EPISODE ATTRIBUTION SUMMARY")
    print("=" * 80)

    print(
        f"Episodes evaluated: {unique_episodes}"
    )

    print(
        f"Issue-level results: {len(result)}"
    )

    print(
        f"Issues contributing >= 10%: {strong_10}"
    )

    print(
        f"Issues contributing >= 20%: {strong_20}"
    )

    # ========================================================
    # TOP THREE PER EPISODE
    # ========================================================

    print("\n")
    print("=" * 80)
    print("TOP THREE ISSUES PER EPISODE")
    print("=" * 80)

    top = result[
        result["rank"] <= 3
    ][
        [
            "country_a",
            "country_b",
            "episode_start",
            "episode_end",
            "peak_change_year",
            "rank",
            "issue",
            "contribution_percent",
            "issue_direction",
        ]
    ]

    print(
        top.to_string(index=False)
    )

    # ========================================================
    # INTERPRETATION
    # ========================================================

    print("\n")
    print("=" * 80)
    print("INTERPRETATION")
    print("=" * 80)

    print(
        "Attribution is calculated at the temporal-episode level."
    )

    print(
        "This prevents multiple change points inside the same "
        "episode from being treated as independent explanations."
    )

    print(
        "Contribution percentages describe the relative share "
        "of absolute issue-level movement."
    )

    print(
        "They do NOT establish causality."
    )

    print(
        "\nSaved episode attribution:"
        f" {OUTPUT_FILE.name}"
    )

    print(
        "\nTEMPORAL EPISODE ISSUE ATTRIBUTION COMPLETE"
    )

    print("=" * 80)


if __name__ == "__main__":
    main()