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
    Standardized difference between two windows.

    Uses pooled standard deviation.
    """

    if before.empty or after.empty:
        return 0.0

    mean_before = _mean(before)
    mean_after = _mean(after)

    std_before = _std(before)
    std_after = _std(after)

    pooled = math.sqrt(
        (
            std_before ** 2
            + std_after ** 2
        )
        / 2.0
    )

    difference = abs(
        mean_after - mean_before
    )

    if pooled == 0:
        return (
            difference
            if difference > 0
            else 0.0
        )

    return difference / pooled


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
    country_column: str = "ms_code",
    issue_column: str = "subject",
    before_window: int = 3,
    after_window: int = 3,
    magnitude_threshold: float = 0.3,
    effect_threshold: float = 0.8,
    persistence_window: int = 3,
) -> pd.DataFrame:
    """
    Detect candidate and confirmed change points.

    Parameters
    ----------
    df:
        Issue-level country position time series.

    value_column:
        Numeric position score.

    before_window:
        Number of observations used before a candidate.

    after_window:
        Number of observations used after a candidate.

    magnitude_threshold:
        Minimum absolute change in normalized position score.
        Position scores use the [-1, +1] scale.

    effect_threshold:
        Minimum standardized effect size.

    persistence_window:
        Minimum number of subsequent observations required
        for confirmation.
    """

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

            if (
                magnitude
                < magnitude_threshold
                or effect
                < effect_threshold
            ):
                continue

            persistence = (
                _persistence_score(
                    values,
                    index,
                    mean_before,
                    magnitude_threshold,
                    persistence_window,
                )
            )

            confirmed = (
                persistence
                >= persistence_window
            )

            # Confidence is deliberately transparent:
            # magnitude, effect and persistence contribute.
            magnitude_score = min(
                magnitude / 30.0,
                1.0,
            )

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
                    "ms_code": country,
                    "subject": issue,
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
                    "confirmed": confirmed,
                    "confidence": confidence,
                }
            )

    if not rows:
        return pd.DataFrame(
            columns=[
                "ms_code",
                "subject",
                "change_year",
                "mean_before",
                "mean_after",
                "change_magnitude",
                "effect_size",
                "persistence",
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
        "ms_code",
        "subject",
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
                "ms_code",
                "subject",
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
        ["ms_code", "subject"],
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
                "ms_code",
                "subject",
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