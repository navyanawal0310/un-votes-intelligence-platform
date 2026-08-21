"""
CHANGE-POINT EXPLANATION

Explains why an already-detected temporal change point occurred.

This script DOES NOT detect new change points.
It only attributes an existing change point to the issues
that changed most around that year.

Inputs:
    temporal_alignment_change_points.csv
    country_pair_alignment.csv

Expected country_pair_alignment columns:
    country_a
    country_b
    issue
    year
    alignment_score

Output:
    change_point_explanations.csv

Method:
    For every detected change point:

        before = mean alignment during the 3 years before
        after  = mean alignment during the 3 years after

        issue_change = after - before

    Issues are ranked by absolute issue_change.

This deliberately uses one simple attribution rule.
"""

from pathlib import Path
import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parent

CHANGE_POINT_FILE = (
    ROOT / "temporal_alignment_change_points.csv"
)

ALIGNMENT_FILE = (
    ROOT / "country_pair_alignment.csv"
)

OUTPUT_FILE = (
    ROOT / "change_point_explanations.csv"
)

WINDOW_YEARS = 3
TOP_ISSUES = 5


def load_change_points():
    if not CHANGE_POINT_FILE.exists():
        raise FileNotFoundError(
            f"Missing file: {CHANGE_POINT_FILE}"
        )

    df = pd.read_csv(CHANGE_POINT_FILE)

    required = {
        "country_a",
        "country_b",
        "change_year",
    }

    missing = sorted(required - set(df.columns))

    if missing:
        raise ValueError(
            f"Change-point file is missing columns: {missing}"
        )

    df["change_year"] = pd.to_numeric(
        df["change_year"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["change_year"]
    ).copy()

    df["change_year"] = df["change_year"].astype(int)

    return df


def load_alignment():
    if not ALIGNMENT_FILE.exists():
        raise FileNotFoundError(
            f"Missing file: {ALIGNMENT_FILE}"
        )

    df = pd.read_csv(ALIGNMENT_FILE)

    required = {
        "country_a",
        "country_b",
        "issue",
        "year",
        "alignment_score",
    }

    missing = sorted(required - set(df.columns))

    if missing:
        raise ValueError(
            f"Alignment file is missing columns: {missing}"
        )

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
            "year",
            "alignment_score",
        ]
    ).copy()

    df["year"] = df["year"].astype(int)

    return df


def pair_key(a, b):
    return tuple(
        sorted(
            [
                str(a).strip(),
                str(b).strip(),
            ]
        )
    )


def get_pair_data(
    alignment,
    country_a,
    country_b,
):
    key = pair_key(
        country_a,
        country_b,
    )

    mask = alignment.apply(
        lambda r: pair_key(
            r["country_a"],
            r["country_b"],
        ) == key,
        axis=1,
    )

    return alignment[mask].copy()


def calculate_issue_changes(
    pair_data,
    change_year,
):
    """
    Calculate issue-level alignment changes around
    the detected change point.
    """

    before = pair_data[
        (pair_data["year"] >= change_year - WINDOW_YEARS)
        & (pair_data["year"] < change_year)
    ].copy()

    after = pair_data[
        (pair_data["year"] > change_year)
        & (pair_data["year"] <= change_year + WINDOW_YEARS)
    ].copy()

    if before.empty or after.empty:
        return pd.DataFrame()

    before_issue = (
        before
        .groupby("issue")["alignment_score"]
        .mean()
        .rename("before_alignment")
    )

    after_issue = (
        after
        .groupby("issue")["alignment_score"]
        .mean()
        .rename("after_alignment")
    )

    result = pd.concat(
        [
            before_issue,
            after_issue,
        ],
        axis=1,
    ).dropna()

    if result.empty:
        return result

    result["issue_change"] = (
        result["after_alignment"]
        - result["before_alignment"]
    )

    result["absolute_issue_change"] = (
        result["issue_change"].abs()
    )

    result = result.sort_values(
        "absolute_issue_change",
        ascending=False,
    )

    return result.reset_index()


def explain_change_point(
    change_point,
    alignment,
):
    country_a = str(
        change_point["country_a"]
    ).strip()

    country_b = str(
        change_point["country_b"]
    ).strip()

    change_year = int(
        change_point["change_year"]
    )

    pair_data = get_pair_data(
        alignment,
        country_a,
        country_b,
    )

    issue_changes = calculate_issue_changes(
        pair_data,
        change_year,
    )

    if issue_changes.empty:
        return []

    issue_changes = issue_changes.head(
        TOP_ISSUES
    )

    rows = []

    for rank, (_, row) in enumerate(
        issue_changes.iterrows(),
        start=1,
    ):

        rows.append(
            {
                "country_a": country_a,
                "country_b": country_b,
                "change_year": change_year,
                "issue_rank": rank,
                "issue": row["issue"],
                "before_alignment": row[
                    "before_alignment"
                ],
                "after_alignment": row[
                    "after_alignment"
                ],
                "issue_change": row[
                    "issue_change"
                ],
                "absolute_issue_change": row[
                    "absolute_issue_change"
                ],
            }
        )

    return rows


def print_results(results):
    if results.empty:
        print(
            "\nNo issue-level explanations "
            "could be calculated."
        )
        return

    display = results.copy()

    numeric_columns = [
        "before_alignment",
        "after_alignment",
        "issue_change",
        "absolute_issue_change",
    ]

    for column in numeric_columns:
        display[column] = pd.to_numeric(
            display[column],
            errors="coerce",
        ).round(3)

    print("\n")
    print("=" * 110)
    print("CHANGE-POINT ISSUE EXPLANATIONS")
    print("=" * 110)

    print(
        display.to_string(
            index=False
        )
    )


def print_summary(results, change_points):
    print("\n")
    print("=" * 80)
    print("EXPLANATION SUMMARY")
    print("=" * 80)

    print(
        f"Change points evaluated: "
        f"{len(change_points)}"
    )

    if results.empty:
        print(
            "Change points with issue-level "
            "explanations: 0"
        )
        return

    explained_pairs = (
        results[
            [
                "country_a",
                "country_b",
                "change_year",
            ]
        ]
        .drop_duplicates()
    )

    print(
        f"Change points explained: "
        f"{len(explained_pairs)}"
    )

    print(
        f"Top issues reported per change point: "
        f"{TOP_ISSUES}"
    )

    print(
        f"Attribution window: "
        f"{WINDOW_YEARS} years before vs "
        f"{WINDOW_YEARS} years after"
    )

    print(
        "\nInterpretation:"
    )

    print(
        "Issues are ranked by the absolute change "
        "in alignment around an EXISTING change point."
    )

    print(
        "This does not claim causality. It identifies "
        "which issues contributed most to the observed "
        "voting-alignment movement."
    )


def main():

    print("=" * 80)
    print("CHANGE-POINT EXPLANATION")
    print("=" * 80)

    change_points = load_change_points()

    alignment = load_alignment()

    print(
        f"Change points loaded: "
        f"{len(change_points)}"
    )

    print(
        f"Alignment observations loaded: "
        f"{len(alignment)}"
    )

    print(
        f"Attribution window: "
        f"{WINDOW_YEARS} years"
    )

    results = []

    for _, change_point in change_points.iterrows():

        rows = explain_change_point(
            change_point,
            alignment,
        )

        results.extend(rows)

    results = pd.DataFrame(
        results
    )

    print_results(results)

    print_summary(
        results,
        change_points,
    )

    results.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("\n")
    print("=" * 80)
    print(
        f"Saved explanation: "
        f"{OUTPUT_FILE.name}"
    )
    print(
        "CHANGE-POINT EXPLANATION COMPLETE"
    )
    print("=" * 80)


if __name__ == "__main__":
    main()