from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

EPISODE_FILE = (
    BASE_DIR / "temporal_alignment_change_episodes.csv"
)

OUTPUT_FILE = (
    BASE_DIR / "temporal_issue_attribution_robustness.csv"
)

WINDOWS = [2, 3, 5]
MIN_OBSERVATIONS = 2
TOP_N = 3


# ============================================================
# LOADERS
# ============================================================

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
            f"Episode file missing columns: {sorted(missing)}"
        )

    for column in [
        "episode_start",
        "episode_end",
        "peak_change_year",
    ]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    return df.dropna(
        subset=[
            "country_a",
            "country_b",
            "episode_start",
            "episode_end",
            "peak_change_year",
        ]
    ).copy()


def load_alignment(country_a, country_b):

    path = (
        BASE_DIR
        / f"alignment_{country_a}_{country_b}.csv"
    )

    if not path.exists():

        # Try reverse ordering as fallback
        reverse_path = (
            BASE_DIR
            / f"alignment_{country_b}_{country_a}.csv"
        )

        if reverse_path.exists():
            path = reverse_path
        else:
            print(
                f"WARNING: Missing alignment file for "
                f"{country_a}-{country_b}"
            )
            return None

    df = pd.read_csv(path)

    required = {
        "issue",
        "year",
        "alignment_score",
    }

    missing = required - set(df.columns)

    if missing:
        print(
            f"WARNING: {path.name} missing "
            f"{sorted(missing)}"
        )
        return None

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df["alignment_score"] = pd.to_numeric(
        df["alignment_score"],
        errors="coerce",
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
# ISSUE ATTRIBUTION FOR ONE WINDOW
# ============================================================

def calculate_attribution(
    alignment,
    episode_start,
    episode_end,
    window,
):

    results = []

    for issue in (
        alignment["issue"]
        .dropna()
        .astype(str)
        .unique()
    ):

        issue_df = alignment[
            alignment["issue"].astype(str) == issue
        ].copy()

        before = issue_df[
            (issue_df["year"] >= episode_start - window)
            &
            (issue_df["year"] < episode_start)
        ]

        after = issue_df[
            (issue_df["year"] > episode_end)
            &
            (issue_df["year"] <= episode_end + window)
        ]

        if (
            len(before) < MIN_OBSERVATIONS
            or len(after) < MIN_OBSERVATIONS
        ):
            continue

        mean_before = (
            before["alignment_score"].mean()
        )

        mean_after = (
            after["alignment_score"].mean()
        )

        shift = mean_after - mean_before

        results.append({
            "issue": issue,
            "mean_before": mean_before,
            "mean_after": mean_after,
            "shift": shift,
            "absolute_shift": abs(shift),
            "direction": (
                "INCREASING"
                if shift > 0
                else
                "DECREASING"
                if shift < 0
                else
                "STABLE"
            ),
        })

    if not results:
        return pd.DataFrame()

    result = pd.DataFrame(results)

    total = result["absolute_shift"].sum()

    if total > 0:
        result["contribution_percent"] = (
            result["absolute_shift"] / total * 100
        )
    else:
        result["contribution_percent"] = 0.0

    result = result.sort_values(
        "absolute_shift",
        ascending=False,
    ).reset_index(drop=True)

    result["rank"] = (
        np.arange(len(result)) + 1
    )

    return result


# ============================================================
# RANK CORRELATION
# ============================================================

def calculate_rank_correlation(
    attribution_a,
    attribution_b,
):

    if attribution_a.empty or attribution_b.empty:
        return np.nan

    a = attribution_a[
        ["issue", "rank"]
    ].copy()

    b = attribution_b[
        ["issue", "rank"]
    ].copy()

    merged = a.merge(
        b,
        on="issue",
        suffixes=("_a", "_b"),
    )

    if len(merged) < 2:
        return np.nan

    return merged[
        ["rank_a", "rank_b"]
    ].corr(method="spearman").iloc[0, 1]


# ============================================================
# TOP-N OVERLAP
# ============================================================

def calculate_top_overlap(
    attribution_a,
    attribution_b,
    top_n=3,
):

    if attribution_a.empty or attribution_b.empty:
        return np.nan

    top_a = set(
        attribution_a.head(top_n)["issue"]
    )

    top_b = set(
        attribution_b.head(top_n)["issue"]
    )

    if not top_a and not top_b:
        return np.nan

    union = top_a | top_b

    if not union:
        return 0.0

    return len(top_a & top_b) / len(union)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("TEMPORAL ISSUE ATTRIBUTION ROBUSTNESS")
    print("=" * 80)

    episodes = load_episodes()

    print(
        f"\nEpisodes available: {len(episodes)}"
    )

    all_results = []
    summary_results = []

    for _, episode in episodes.iterrows():

        country_a = str(
            episode["country_a"]
        ).upper()

        country_b = str(
            episode["country_b"]
        ).upper()

        episode_start = int(
            episode["episode_start"]
        )

        episode_end = int(
            episode["episode_end"]
        )

        peak_year = int(
            episode["peak_change_year"]
        )

        pair = f"{country_a}-{country_b}"

        print("\n" + "=" * 80)

        print(
            f"{pair} | "
            f"{episode_start}-{episode_end} | "
            f"Peak: {peak_year}"
        )

        alignment = load_alignment(
            country_a,
            country_b,
        )

        if alignment is None:
            continue

        window_results = {}

        # ----------------------------------------------------
        # RUN ALL WINDOWS
        # ----------------------------------------------------

        for window in WINDOWS:

            attribution = calculate_attribution(
                alignment=alignment,
                episode_start=episode_start,
                episode_end=episode_end,
                window=window,
            )

            window_results[window] = attribution

            if attribution.empty:
                print(
                    f"\nWindow {window} years: "
                    "NO RESULT"
                )
                continue

            print(
                f"\nWindow: {window} years"
            )

            print(
                attribution[
                    [
                        "rank",
                        "issue",
                        "contribution_percent",
                        "direction",
                    ]
                ]
                .head(TOP_N)
                .to_string(index=False)
            )

            for _, row in attribution.iterrows():

                all_results.append({
                    "country_a": country_a,
                    "country_b": country_b,
                    "episode_start": episode_start,
                    "episode_end": episode_end,
                    "peak_change_year": peak_year,
                    "window_years": window,
                    "rank": row["rank"],
                    "issue": row["issue"],
                    "contribution_percent": (
                        row["contribution_percent"]
                    ),
                    "direction": row["direction"],
                    "absolute_shift": (
                        row["absolute_shift"]
                    ),
                })

        # ----------------------------------------------------
        # COMPARE WINDOWS
        # ----------------------------------------------------

        attr_2 = window_results.get(
            2,
            pd.DataFrame(),
        )

        attr_3 = window_results.get(
            3,
            pd.DataFrame(),
        )

        attr_5 = window_results.get(
            5,
            pd.DataFrame(),
        )

        top_overlap_2_3 = (
            calculate_top_overlap(
                attr_2,
                attr_3,
                TOP_N,
            )
        )

        top_overlap_3_5 = (
            calculate_top_overlap(
                attr_3,
                attr_5,
                TOP_N,
            )
        )

        top_overlap_2_5 = (
            calculate_top_overlap(
                attr_2,
                attr_5,
                TOP_N,
            )
        )

        rank_corr_2_3 = (
            calculate_rank_correlation(
                attr_2,
                attr_3,
            )
        )

        rank_corr_3_5 = (
            calculate_rank_correlation(
                attr_3,
                attr_5,
            )
        )

        rank_corr_2_5 = (
            calculate_rank_correlation(
                attr_2,
                attr_5,
            )
        )

        # ----------------------------------------------------
        # TOP-1 CONSISTENCY
        # ----------------------------------------------------

        top1 = []

        for attr in [
            attr_2,
            attr_3,
            attr_5,
        ]:

            if not attr.empty:
                top1.append(
                    attr.iloc[0]["issue"]
                )

        if len(top1) >= 2:

            top1_consistency = (
                len(set(top1)) == 1
            )

        else:

            top1_consistency = False

        # ----------------------------------------------------
        # DIRECTION CONSISTENCY FOR TOP ISSUE
        # ----------------------------------------------------

        top_directions = []

        for attr in [
            attr_2,
            attr_3,
            attr_5,
        ]:

            if not attr.empty:
                top_directions.append(
                    attr.iloc[0]["direction"]
                )

        if len(top_directions) >= 2:

            direction_consistency = (
                len(set(top_directions)) == 1
            )

        else:

            direction_consistency = False

        summary_results.append({
            "country_a": country_a,
            "country_b": country_b,
            "episode_start": episode_start,
            "episode_end": episode_end,
            "peak_change_year": peak_year,
            "top1_consistent": top1_consistency,
            "top_issue_direction_consistent": (
                direction_consistency
            ),
            "top3_overlap_2_vs_3": top_overlap_2_3,
            "top3_overlap_3_vs_5": top_overlap_3_5,
            "top3_overlap_2_vs_5": top_overlap_2_5,
            "rank_correlation_2_vs_3": rank_corr_2_3,
            "rank_correlation_3_vs_5": rank_corr_3_5,
            "rank_correlation_2_vs_5": rank_corr_2_5,
        })

    # ========================================================
    # SAVE DETAILED RESULTS
    # ========================================================

    if all_results:

        detailed = pd.DataFrame(
            all_results
        )

        detailed.to_csv(
            OUTPUT_FILE,
            index=False,
        )

    else:

        detailed = pd.DataFrame()

    # ========================================================
    # SUMMARY
    # ========================================================

    summary = pd.DataFrame(
        summary_results
    )

    summary_file = (
        BASE_DIR
        / "temporal_issue_attribution_robustness_summary.csv"
    )

    if not summary.empty:

        summary.to_csv(
            summary_file,
            index=False,
        )

    print("\n")
    print("=" * 80)
    print("ROBUSTNESS SUMMARY")
    print("=" * 80)

    if summary.empty:

        print(
            "No robustness comparisons could be calculated."
        )

        return

    print(
        f"Episodes evaluated: {len(summary)}"
    )

    print(
        "Top-1 issue consistent: "
        f"{summary['top1_consistent'].sum()} / "
        f"{len(summary)}"
    )

    print(
        "Top-issue direction consistent: "
        f"{summary['top_issue_direction_consistent'].sum()} / "
        f"{len(summary)}"
    )

    print(
        "\nMean Top-3 overlap:"
    )

    print(
        f"  2 vs 3 years: "
        f"{summary['top3_overlap_2_vs_3'].mean():.3f}"
    )

    print(
        f"  3 vs 5 years: "
        f"{summary['top3_overlap_3_vs_5'].mean():.3f}"
    )

    print(
        f"  2 vs 5 years: "
        f"{summary['top3_overlap_2_vs_5'].mean():.3f}"
    )

    print(
        "\nMean rank correlation:"
    )

    print(
        f"  2 vs 3 years: "
        f"{summary['rank_correlation_2_vs_3'].mean():.3f}"
    )

    print(
        f"  3 vs 5 years: "
        f"{summary['rank_correlation_3_vs_5'].mean():.3f}"
    )

    print(
        f"  2 vs 5 years: "
        f"{summary['rank_correlation_2_vs_5'].mean():.3f}"
    )

    print("\n")
    print("=" * 80)
    print("INTERPRETATION")
    print("=" * 80)

    print(
        "Attribution robustness tests whether the leading "
        "issue-level explanation remains reasonably stable "
        "when the before/after window changes."
    )

    print(
        "High Top-3 overlap and high rank correlation indicate "
        "stable attribution."
    )

    print(
        "Low overlap indicates that the attribution is sensitive "
        "to the selected temporal window."
    )

    print(
        "This is a robustness assessment, not a causal test."
    )

    print(
        f"\nSaved detailed results: "
        f"{OUTPUT_FILE.name}"
    )

    print(
        f"Saved summary: "
        f"{summary_file.name}"
    )

    print(
        "\nTEMPORAL ISSUE ATTRIBUTION ROBUSTNESS COMPLETE"
    )

    print("=" * 80)


if __name__ == "__main__":
    main()