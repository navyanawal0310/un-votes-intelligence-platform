"""
Temporal change-point detection for UN voting positions.

Detects persistent structural shifts in a country's
issue-level voting position.

Outputs distinguish:
- candidate changes
- confirmed changes
- magnitude
- effect size
- persistence
- confidence

This module detects statistical changes only. It does not
claim that a detected change has a specific geopolitical cause.
"""

from __future__ import annotations

import math

import pandas as pd


def _mean(values: pd.Series) -> float:
    return float(values.mean())


def _std(values: pd.Series) -> float:
    value = float(values.std(ddof=1))

    if math.isnan(value):
        return 0.0

    return value

def _effect_size(
    before: pd.Series,
    after: pd.Series,
) -> float:
    """
    Standardized mean difference between two windows.

    Uses pooled standard deviation.

    Returns 0 when the pooled standard deviation is
    effectively zero, because a standardized effect size
    is undefined in that case.
    """

    if before.empty or after.empty:
        return 0.0

    before = pd.to_numeric(
        before,
        errors="coerce",
    ).dropna()

    after = pd.to_numeric(
        after,
        errors="coerce",
    ).dropna()

    if before.empty or after.empty:
        return 0.0

    mean_before = float(before.mean())
    mean_after = float(after.mean())

    std_before = float(before.std(ddof=1))
    std_after = float(after.std(ddof=1))

    pooled = math.sqrt(
        (
            std_before ** 2
            + std_after ** 2
        ) / 2.0
    )

    difference = abs(
        mean_after - mean_before
    )

    # Standardized effect size is undefined
    # when both windows have effectively zero variance.
    if pooled <= 1e-12:
        return 0.0

    return difference / pooled

def _pooled_std(
    before: pd.Series,
    after: pd.Series,
) -> float:
    """
    Calculate pooled standard deviation for the
    before/after windows.

    Used to identify near-deterministic voting shifts
    where standardized effect size is undefined.
    """

    if before.empty or after.empty:
        return 0.0

    before = pd.to_numeric(
        before,
        errors="coerce",
    ).dropna()

    after = pd.to_numeric(
        after,
        errors="coerce",
    ).dropna()

    if before.empty or after.empty:
        return 0.0

    std_before = float(
        before.std(ddof=1)
    )

    std_after = float(
        after.std(ddof=1)
    )

    if math.isnan(std_before):
        std_before = 0.0

    if math.isnan(std_after):
        std_after = 0.0

    return math.sqrt(
        (
            std_before ** 2
            + std_after ** 2
        ) / 2.0
    )

def _persistence_score(
    values: pd.Series,
    change_year_index: int,
    baseline_mean: float,
    magnitude_threshold: float,
    persistence_window: int,
) -> int:
    """
    Count consecutive observations after the candidate
    point that remain materially different from the
    pre-change baseline.
    """

    if persistence_window <= 0:
        return 0

    after = values.iloc[
        change_year_index:
    ]

    count = 0

    for value in after:

        if (
            abs(
                float(value)
                - baseline_mean
            )
            >= magnitude_threshold
        ):
            count += 1

            if count >= persistence_window:
                break

        else:
            break

    return count


def detect_change_points(
    df: pd.DataFrame,
    value_column: str = "position_score",
    year_column: str = "year",
    country_column: str = "country_code",
    issue_column: str = "issue",
    before_window: int = 3,
    after_window: int = 3,
    magnitude_threshold: float = 0.4,
    effect_threshold: float = 0.8,
    persistence_window: int = 3,
) -> pd.DataFrame:

    required = {
        value_column,
        year_column,
        country_column,
        issue_column,
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            "Missing required columns: "
            f"{sorted(missing)}"
        )

    working = df.copy()

    working[value_column] = pd.to_numeric(
        working[value_column],
        errors="coerce",
    )

    working[year_column] = pd.to_numeric(
        working[year_column],
        errors="coerce",
    )

    working = (
        working
        .dropna(
            subset=[
                value_column,
                year_column,
            ]
        )
        .sort_values(
            [
                country_column,
                issue_column,
                year_column,
            ]
        )
    )

    rows = []

    grouped = working.groupby(
        [
            country_column,
            issue_column,
        ],
        dropna=False,
    )

    for (
        country,
        issue,
    ), group in grouped:

        group = (
            group
            .drop_duplicates(
                subset=[year_column]
            )
            .sort_values(year_column)
            .reset_index(drop=True)
        )

        values = group[
            value_column
        ].reset_index(drop=True)

        years = group[
            year_column
        ].reset_index(drop=True)

        minimum_length = (
            before_window
            + after_window
            + persistence_window
        )

        if len(group) < minimum_length:
            continue

        for index in range(
            before_window,
            len(group) - after_window + 1,
        ):

            before = values.iloc[
                index - before_window:
                index
            ]

            after = values.iloc[
                index:
                index + after_window
            ]

            mean_before = _mean(before)
            mean_after = _mean(after)

            magnitude = abs(
                mean_after
                - mean_before
            )

            effect = _effect_size(
                before,
                after,
            )

            pooled_std = _pooled_std(
                before,
                after,
            )

            low_variance_shift = (
                pooled_std <= 1e-12
            )

            passes_statistical_rule = (
                magnitude >= magnitude_threshold
                and effect >= effect_threshold
            )

            passes_deterministic_rule = (
                magnitude >= magnitude_threshold
                and low_variance_shift
            )

            if not (
                passes_statistical_rule
                or passes_deterministic_rule
            ):
                continue

            persistence = _persistence_score(
                values,
                index,
                mean_before,
                magnitude_threshold,
                persistence_window,
            )

            confirmed = (
                persistence
                >= persistence_window
            )

            magnitude_score = min(
                magnitude / 2.0,
                1.0,
            )

            if low_variance_shift:
                effect_score = 1.0
            else:
                effect_score = min(
                    effect / 2.0,
                    1.0,
                )

            persistence_score = min(
                persistence
                / max(
                    persistence_window,
                    1,
                ),
                1.0,
            )

            confidence = round(
                (
                    0.35 * magnitude_score
                    + 0.35 * effect_score
                    + 0.30 * persistence_score
                ),
                3,
            )

            rows.append(
                {
                    "country_code": country,
                    "issue": issue,
                    "change_year": int(
                        years.iloc[index]
                    ),
                    "mean_before": round(
                        mean_before,
                        3,
                    ),
                    "mean_after": round(
                        mean_after,
                        3,
                    ),
                    "change_magnitude": round(
                        magnitude,
                        3,
                    ),
                    "effect_size": round(
                        effect,
                        3,
                    ),
                    "persistence": persistence,
                    "low_variance_shift":
                        low_variance_shift,
                    "confirmed": confirmed,
                    "confidence": confidence,
                }
            )

    if not rows:
        return pd.DataFrame(
            columns=[
                "country_code",
                "issue",
                "change_year",
                "mean_before",
                "mean_after",
                "change_magnitude",
                "effect_size",
                "persistence",
                "low_variance_shift",
                "confirmed",
                "confidence",
            ]
        )

    return (
        pd.DataFrame(rows)
        .sort_values(
            [
                "confirmed",
                "confidence",
                "change_magnitude",
            ],
            ascending=False,
        )
        .reset_index(drop=True)
    )
def consolidate_change_points(
    changes: pd.DataFrame,
    min_separation: int = 3,
) -> pd.DataFrame:
    """
    Consolidate nearby candidate detections belonging
    to the same structural transition.

    The highest-confidence detection is retained
    within each temporal cluster.
    """

    if changes.empty:
        return changes.copy()

    required = {
        "country_code",
        "issue",
        "change_year",
        "confidence",
    }

    missing = required - set(changes.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    if min_separation < 1:
        raise ValueError(
            "min_separation must be >= 1"
        )

    working = (
        changes
        .copy()
        .sort_values(
            [
                "country_code",
                "issue",
                "change_year",
                "confidence",
            ],
            ascending=[
                True,
                True,
                True,
                False,
            ],
        )
        .reset_index(drop=True)
    )

    kept = []

    for _, group in working.groupby(
        ["country_code", "issue"],
        dropna=False,
    ):
        cluster = []

        for _, row in group.iterrows():
            year = int(row["change_year"])

            if not cluster:
                cluster = [row]
                continue

            previous_year = int(
                cluster[-1]["change_year"]
            )

            if year - previous_year <= min_separation:
                cluster.append(row)
            else:
                best = max(
                    cluster,
                    key=lambda r: float(r["confidence"]),
                )
                kept.append(best)
                cluster = [row]

        if cluster:
            best = max(
                cluster,
                key=lambda r: float(r["confidence"]),
            )
            kept.append(best)

    if not kept:
        return working.iloc[0:0].copy()

    return (
        pd.DataFrame(kept)
        .sort_values(
            [
                "country_code",
                "issue",
                "change_year",
            ]
        )
        .reset_index(drop=True)
    )

def confirmed_change_points(
    changes: pd.DataFrame,
) -> pd.DataFrame:
    """
    Return only persistent, confirmed changes.
    """

    if changes.empty:
        return changes.copy()

    return (
        changes[
            changes["confirmed"] == True
        ]
        .copy()
        .reset_index(drop=True)
    )


def change_point_summary(
    changes: pd.DataFrame,
) -> dict[str, float | int]:
    """
    Produce aggregate detector statistics.
    """

    if changes.empty:
        return {
            "candidate_count": 0,
            "confirmed_count": 0,
            "confirmation_rate": 0.0,
            "mean_confidence": 0.0,
            "mean_magnitude": 0.0,
        }

    candidate_count = len(changes)

    confirmed_count = int(
        changes["confirmed"].sum()
    )

    return {
        "candidate_count": candidate_count,
        "confirmed_count": confirmed_count,
        "confirmation_rate": round(
            confirmed_count
            / candidate_count
            * 100.0,
            2,
        ),
        "mean_confidence": round(
            float(
                changes["confidence"].mean()
            ),
            3,
        ),
        "mean_magnitude": round(
            float(
                changes[
                    "change_magnitude"
                ].mean()
            ),
            3,
        ),
    }