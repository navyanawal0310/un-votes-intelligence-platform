from __future__ import annotations

import pandas as pd
import numpy as np
from pathlib import Path

GROUND_TRUTH = Path(
    "data/validation/temporal_ground_truth.csv"
)

ALIGNMENT_DIR = Path(".")

OUTPUT = Path(
    "temporal_event_signal_diagnostic.csv"
)


COUNTRY_PAIRS = [
    ("CHN", "RUS"),
    ("CHN", "USA"),
    ("IND", "CHN"),
    ("IND", "RUS"),
    ("IND", "USA"),
    ("USA", "RUS"),
]


def load_alignment(country_a, country_b):

    path = (
        ALIGNMENT_DIR
        / f"alignment_{country_a}_{country_b}.csv"
    )

    if not path.exists():

        reverse = (
            ALIGNMENT_DIR
            / f"alignment_{country_b}_{country_a}.csv"
        )

        if reverse.exists():
            path = reverse
        else:
            return pd.DataFrame()

    df = pd.read_csv(path)

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    return df


def clean_year(series):

    return pd.to_numeric(
        series,
        errors="coerce"
    )


def clean_alignment(df):

    if df.empty:
        return df

    if "year" not in df.columns:
        return pd.DataFrame()

    df["year"] = clean_year(
        df["year"]
    )

    if "alignment_score" not in df.columns:

        if {
            "score_a",
            "score_b",
        }.issubset(df.columns):

            df["alignment_score"] = (
                1
                - (
                    df["score_a"]
                    - df["score_b"]
                ).abs()
            )

        else:
            return pd.DataFrame()

    df["alignment_score"] = pd.to_numeric(
        df["alignment_score"],
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            "year",
            "alignment_score",
        ]
    )

    return (
        df
        .sort_values("year")
        .drop_duplicates(
            "year",
            keep="last"
        )
    )


def calculate_signal(
    df,
    event_start,
    event_end,
    window=5,
):

    if df.empty:
        return None

    event_start = int(event_start)
    event_end = int(event_end)

    pre = df[
        (df["year"] >= event_start - window)
        &
        (df["year"] < event_start)
    ]

    event = df[
        (df["year"] >= event_start)
        &
        (df["year"] <= event_end)
    ]

    post = df[
        (df["year"] > event_end)
        &
        (df["year"] <= event_end + window)
    ]

    local = df[
        (df["year"] >= event_start - window)
        &
        (df["year"] <= event_end + window)
    ].copy()

    result = {
        "pre_observations": len(pre),
        "event_observations": len(event),
        "post_observations": len(post),

        "pre_mean": np.nan,
        "event_mean": np.nan,
        "post_mean": np.nan,

        "pre_to_event_shift": np.nan,
        "event_to_post_shift": np.nan,

        "max_local_change": np.nan,
        "max_local_change_year": np.nan,

        "local_min": np.nan,
        "local_max": np.nan,
        "local_range": np.nan,
    }

    if not pre.empty:
        result["pre_mean"] = pre[
            "alignment_score"
        ].mean()

    if not event.empty:
        result["event_mean"] = event[
            "alignment_score"
        ].mean()

    if not post.empty:
        result["post_mean"] = post[
            "alignment_score"
        ].mean()

    if (
        not pd.isna(result["pre_mean"])
        and not pd.isna(result["event_mean"])
    ):
        result[
            "pre_to_event_shift"
        ] = (
            result["event_mean"]
            - result["pre_mean"]
        )

    if (
        not pd.isna(result["event_mean"])
        and not pd.isna(result["post_mean"])
    ):
        result[
            "event_to_post_shift"
        ] = (
            result["post_mean"]
            - result["event_mean"]
        )

    if not local.empty:

        local = local.sort_values(
            "year"
        )

        local["annual_change"] = (
            local["alignment_score"]
            .diff()
        )

        changes = local[
            "annual_change"
        ].abs()

        if not changes.dropna().empty:

            idx = changes.idxmax()

            result[
                "max_local_change"
            ] = changes.loc[idx]

            result[
                "max_local_change_year"
            ] = local.loc[
                idx,
                "year"
            ]

        result["local_min"] = local[
            "alignment_score"
        ].min()

        result["local_max"] = local[
            "alignment_score"
        ].max()

        result["local_range"] = (
            result["local_max"]
            - result["local_min"]
        )

    return result


def main():

    print("=" * 90)
    print("TEMPORAL EVENT SIGNAL DIAGNOSTIC")
    print("=" * 90)

    ground_truth = pd.read_csv(
        GROUND_TRUTH
    )

    results = []

    cache = {}

    for _, event in ground_truth.iterrows():

        country_a = event[
            "country_a"
        ]

        country_b = event[
            "country_b"
        ]

        key = (
            country_a,
            country_b,
        )

        if key not in cache:

            cache[key] = clean_alignment(
                load_alignment(
                    country_a,
                    country_b,
                )
            )

        df = cache[key]

        event_start = pd.to_numeric(
            event["event_start"],
            errors="coerce"
        )

        event_end = pd.to_numeric(
            event["event_end"],
            errors="coerce"
        )

        if pd.isna(event_start):
            continue

        if pd.isna(event_end):
            event_end = event_start

        signal = calculate_signal(
            df,
            event_start,
            event_end,
            window=5,
        )

        if signal is None:

            signal = {
                "pre_observations": 0,
                "event_observations": 0,
                "post_observations": 0,
                "pre_mean": np.nan,
                "event_mean": np.nan,
                "post_mean": np.nan,
                "pre_to_event_shift": np.nan,
                "event_to_post_shift": np.nan,
                "max_local_change": np.nan,
                "max_local_change_year": np.nan,
                "local_min": np.nan,
                "local_max": np.nan,
                "local_range": np.nan,
            }

        results.append({
            "country_a": country_a,
            "country_b": country_b,
            "event_start": event_start,
            "event_end": event_end,
            "event_name": event[
                "event_name"
            ],
            **signal,
        })

    result = pd.DataFrame(
        results
    )

    result.to_csv(
        OUTPUT,
        index=False
    )

    print()
    print(
        result.to_string(
            index=False
        )
    )

    print()
    print("=" * 90)
    print("EVENT SIGNAL SUMMARY")
    print("=" * 90)

    events_with_event_observations = (
        result["event_observations"] > 0
    ).sum()

    events_with_pre_event_coverage = (
        (result["pre_observations"] > 0)
        &
        (result["event_observations"] > 0)
    ).sum()

    mean_abs_shift = (
        result["pre_to_event_shift"]
        .abs()
        .mean()
    )

    max_local_change = (
        result["max_local_change"]
        .max()
    )

    print(
        f"Events evaluated: {len(result)}"
    )

    print(
        f"Events with event-period observations: "
        f"{events_with_event_observations}"
    )

    print(
        f"Events with pre + event coverage: "
        f"{events_with_pre_event_coverage}"
    )

    print()

    print(
        f"Mean absolute pre→event shift: "
        f"{mean_abs_shift:.3f}"
    )

    print(
        f"Maximum local annual change: "
        f"{max_local_change:.3f}"
    )

    print()

    print(
        f"Saved diagnostic to: {OUTPUT}"
    )

    print()
    print("=" * 90)
    print(
        "TEMPORAL EVENT SIGNAL DIAGNOSTIC COMPLETE"
    )
    print("=" * 90)

if __name__ == "__main__":
    main()