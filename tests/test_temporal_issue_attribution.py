from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

CHANGE_POINT_FILE = BASE_DIR / "temporal_alignment_change_points.csv"

OUTPUT_FILE = BASE_DIR / "temporal_issue_attribution.csv"

WINDOW_YEARS = 3
MIN_OBSERVATIONS = 2

PAIR_FILES = {
    "IND-RUS": BASE_DIR / "alignment_IND_RUS.csv",
    "IND-USA": BASE_DIR / "alignment_IND_USA.csv",
    "CHN-RUS": BASE_DIR / "alignment_CHN_RUS.csv",
    "CHN-USA": BASE_DIR / "alignment_CHN_USA.csv",
    "IND-CHN": BASE_DIR / "alignment_IND_CHN.csv",
    "USA-RUS": BASE_DIR / "alignment_USA_RUS.csv",
}


# ============================================================
# HELPERS
# ============================================================

def normalize_pair(a, b):
    return f"{str(a).upper()}-{str(b).upper()}"


def load_change_points():
    if not CHANGE_POINT_FILE.exists():
        raise FileNotFoundError(
            f"Missing change-point file:\n{CHANGE_POINT_FILE}"
        )

    df = pd.read_csv(CHANGE_POINT_FILE)

    required = {
        "country_a",
        "country_b",
        "change_year",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Change-point file missing columns: {sorted(missing)}\n"
            f"Available columns: {list(df.columns)}"
        )

    df["change_year"] = pd.to_numeric(
        df["change_year"], errors="coerce"
    )

    df = df.dropna(subset=["change_year"]).copy()

    return df


def load_pair_file(pair, path):
    if not path.exists():
        print(f"WARNING: missing {path}")
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
            f"WARNING: {path.name} missing {sorted(missing)}"
        )
        print(f"Available: {list(df.columns)}")
        return None

    df["year"] = pd.to_numeric(
        df["year"], errors="coerce"
    )

    df["alignment_score"] = pd.to_numeric(
        df["alignment_score"], errors="coerce"
    )

    df = df.dropna(
        subset=["year", "alignment_score", "issue"]
    ).copy()

    return df


def calculate_issue_attribution(
    df,
    change_year,
    country_a,
    country_b,
):
    results = []

    issues = (
        df["issue"]
        .dropna()
        .astype(str)
        .unique()
    )

    for issue in issues:

        issue_df = df[
            df["issue"].astype(str) == issue
        ].copy()

        before = issue_df[
            (issue_df["year"] >= change_year - WINDOW_YEARS)
            & (issue_df["year"] < change_year)
        ]

        after = issue_df[
            (issue_df["year"] > change_year)
            & (issue_df["year"] <= change_year + WINDOW_YEARS)
        ]

        before = before.dropna(
            subset=["alignment_score"]
        )

        after = after.dropna(
            subset=["alignment_score"]
        )

        if (
            len(before) < MIN_OBSERVATIONS
            or len(after) < MIN_OBSERVATIONS
        ):
            continue

        mean_before = before["alignment_score"].mean()
        mean_after = after["alignment_score"].mean()

        issue_shift = mean_after - mean_before
        absolute_shift = abs(issue_shift)

        if issue_shift > 0:
            direction = "INCREASING"
        elif issue_shift < 0:
            direction = "DECREASING"
        else:
            direction = "STABLE"

        results.append({
            "country_a": country_a,
            "country_b": country_b,
            "change_year": int(change_year),
            "issue": issue,
            "before_observations": len(before),
            "after_observations": len(after),
            "mean_before": mean_before,
            "mean_after": mean_after,
            "issue_shift": issue_shift,
            "absolute_shift": absolute_shift,
            "issue_direction": direction,
        })

    if not results:
        return pd.DataFrame()

    result = pd.DataFrame(results)

    total_shift = result["absolute_shift"].sum()

    if total_shift > 0:
        result["share_of_total_change"] = (
            result["absolute_shift"] / total_shift
        )
    else:
        result["share_of_total_change"] = 0.0

    result["contribution_percent"] = (
        result["share_of_total_change"] * 100
    )

    result = result.sort_values(
        "absolute_shift",
        ascending=False
    ).reset_index(drop=True)

    result["rank"] = np.arange(1, len(result) + 1)

    return result


# ============================================================
# MAIN ANALYSIS
# ============================================================

def main():

    print("=" * 80)
    print("TEMPORAL ISSUE-LEVEL ATTRIBUTION")
    print("=" * 80)

    change_points = load_change_points()

    print(
        f"\nChange points evaluated: {len(change_points)}"
    )

    all_results = []

    for _, cp in change_points.iterrows():

        country_a = str(cp["country_a"]).upper()
        country_b = str(cp["country_b"]).upper()

        pair = normalize_pair(
            country_a,
            country_b
        )

        change_year = int(cp["change_year"])

        print("\n" + "-" * 80)
        print(
            f"{pair} | change year: {change_year}"
        )

        path = PAIR_FILES.get(pair)

        if path is None:
            print(
                f"WARNING: no alignment file configured for {pair}"
            )
            continue

        df = load_pair_file(pair, path)

        if df is None:
            continue

        attribution = calculate_issue_attribution(
            df=df,
            change_year=change_year,
            country_a=country_a,
            country_b=country_b,
        )

        if attribution.empty:
            print(
                "No issues met the minimum observation requirement."
            )
            continue

        all_results.append(attribution)

        print("\nTOP ISSUES CONTRIBUTING TO OBSERVED CHANGE")
        print(
            attribution[
                [
                    "issue",
                    "mean_before",
                    "mean_after",
                    "issue_shift",
                    "contribution_percent",
                    "issue_direction",
                ]
            ]
            .head(10)
            .to_string(index=False)
        )

    if not all_results:
        print("\nNo issue-level attribution results produced.")
        return

    result = pd.concat(
        all_results,
        ignore_index=True
    )

    # --------------------------------------------------------
    # Final ranking within each change point
    # --------------------------------------------------------

    result = result.sort_values(
        [
            "country_a",
            "country_b",
            "change_year",
            "absolute_shift",
        ],
        ascending=[True, True, True, False],
    )

    result["rank"] = (
        result
        .groupby(
            [
                "country_a",
                "country_b",
                "change_year",
            ]
        )
        .cumcount()
        + 1
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    result.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n")
    print("=" * 80)
    print("ISSUE ATTRIBUTION SUMMARY")
    print("=" * 80)

    print(
        f"Change points evaluated: "
        f"{result[['country_a','country_b','change_year']].drop_duplicates().shape[0]}"
    )

    print(
        f"Issue-level observations: {len(result)}"
    )

    print(
        f"Issues explaining >= 10% of observed change: "
        f"{(result['contribution_percent'] >= 10).sum()}"
    )

    print(
        f"Issues explaining >= 20% of observed change: "
        f"{(result['contribution_percent'] >= 20).sum()}"
    )

    print("\nTOP CONTRIBUTIONS")

    top = result[
        result["rank"] <= 3
    ][
        [
            "country_a",
            "country_b",
            "change_year",
            "rank",
            "issue",
            "contribution_percent",
            "issue_direction",
        ]
    ]

    print(
        top.to_string(index=False)
    )

    print("\n")
    print("=" * 80)
    print(
        "INTERPRETATION"
    )
    print("=" * 80)

    print(
        "Issue contributions describe the decomposition of the "
        "observed alignment shift."
    )

    print(
        "They do NOT establish that an issue caused the change."
    )

    print(
        f"\nSaved attribution: {OUTPUT_FILE.name}"
    )

    print(
        "TEMPORAL ISSUE ATTRIBUTION COMPLETE"
    )

    print("=" * 80)


if __name__ == "__main__":
    main()