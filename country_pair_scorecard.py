"""
UN VOTES ANALYZER
COUNTRY-PAIR INTELLIGENCE SCORECARD

Purpose
-------
Consolidate validated temporal measurements into one
country-pair intelligence scorecard.

This layer does NOT create new statistical evidence.
It summarizes previously calculated measurements.

Interpretation is descriptive, not causal.
"""

from pathlib import Path
import pandas as pd
import numpy as np


BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# INPUT FILES
# ============================================================

FILES = {
    "summary": "country_pair_alignment_summary.csv",
    "temporal": "country_pair_temporal_alignment.csv",
    "change_points": "temporal_alignment_change_points.csv",
    "ground_truth": "temporal_ground_truth_validation.csv",
    "event_detection": "temporal_event_conditioned_detection.csv",
    "coverage": "temporal_detection_coverage.csv",
    "robustness": "temporal_robustness_analysis.csv",
    "attribution_robustness": "temporal_issue_attribution_robustness_summary.csv",
}


# ============================================================
# THRESHOLDS
# ============================================================

# Deliberately conservative.
# We do not want tiny numerical movements to become
# "improving" or "declining".

TREND_THRESHOLD = 0.05

STRONG_TREND_THRESHOLD = 0.10

HIGH_CONFIDENCE_RECALL = 0.50

MODERATE_CONFIDENCE_RECALL = 0.20


# ============================================================
# LOADING
# ============================================================

def load_file(filename, required=True):

    path = BASE_DIR / filename

    if not path.exists():

        if required:
            print(f"[WARNING] Missing: {filename}")

        return pd.DataFrame()

    try:

        df = pd.read_csv(path)

        print(
            f"[OK] Loaded {filename}: {len(df)} rows"
        )

        return df

    except Exception as exc:

        print(
            f"[WARNING] Could not read {filename}: {exc}"
        )

        return pd.DataFrame()


def load_data():

    data = {}

    for name, filename in FILES.items():

        data[name] = load_file(
            filename,
            required=(name in ["summary", "temporal"])
        )

    return data


# ============================================================
# NORMALIZE COUNTRY PAIRS
# ============================================================

def normalize_pairs(df):

    if df.empty:
        return df

    df = df.copy()

    if "country_a" in df.columns:
        df["country_a"] = (
            df["country_a"]
            .astype(str)
            .str.strip()
        )

    if "country_b" in df.columns:
        df["country_b"] = (
            df["country_b"]
            .astype(str)
            .str.strip()
        )

    if "pair" not in df.columns:

        if (
            "country_a" in df.columns
            and "country_b" in df.columns
        ):

            df["pair"] = (
                df["country_a"]
                + "-"
                + df["country_b"]
            )

    return df


# ============================================================
# TREND INTERPRETATION
# ============================================================

def interpret_trend(change):

    if pd.isna(change):
        return "INSUFFICIENT_EVIDENCE"

    if change > TREND_THRESHOLD:
        return "IMPROVING"

    if change < -TREND_THRESHOLD:
        return "DECLINING"

    return "STABLE"


# ============================================================
# CONFIDENCE
# ============================================================

def calculate_confidence(
    validation_recall,
    coverage,
    robustness_available,
):

    """
    Evidence confidence.

    This is NOT statistical significance.

    Confidence reflects the amount and quality of supporting
    validation evidence available to the analytical pipeline.
    """

    # Strong validation evidence
    if pd.notna(validation_recall):

        if validation_recall >= 0.50:
            confidence = "HIGH"

        elif validation_recall >= 0.20:
            confidence = "MODERATE"

        else:
            confidence = "LOW"

    else:

        # No pair-specific recall available.
        # Do not falsely label the relationship LOW.
        confidence = "MODERATE"

    # Global detection coverage
    if pd.notna(coverage):

        if coverage < 0.20:

            confidence = "LOW"

        elif coverage < 0.50:

            if confidence == "HIGH":
                confidence = "MODERATE"

    # Robustness is supporting evidence, not a requirement.
    #
    # Therefore, absence of a robustness file should not
    # automatically downgrade an otherwise strong result.

    return confidence

# ============================================================
# LATEST ALIGNMENT
# ============================================================

def get_recent_alignment(temporal, pair):

    if temporal.empty:
        return np.nan

    subset = temporal[
        temporal["pair"] == pair
    ].copy()

    if subset.empty:
        return np.nan

    if "window_end" in subset.columns:

        subset["window_end"] = pd.to_numeric(
            subset["window_end"],
            errors="coerce"
        )

        subset = subset.sort_values(
            "window_end"
        )

    if "mean_alignment" not in subset.columns:
        return np.nan

    values = pd.to_numeric(
        subset["mean_alignment"],
        errors="coerce"
    ).dropna()

    if values.empty:
        return np.nan

    return float(values.iloc[-1])


# ============================================================
# HISTORICAL ALIGNMENT
# ============================================================

def get_historical_alignment(temporal, pair):

    if temporal.empty:
        return np.nan

    subset = temporal[
        temporal["pair"] == pair
    ].copy()

    if subset.empty:
        return np.nan

    if "window_start" in subset.columns:

        subset["window_start"] = pd.to_numeric(
            subset["window_start"],
            errors="coerce"
        )

        subset = subset.sort_values(
            "window_start"
        )

    if "mean_alignment" not in subset.columns:
        return np.nan

    values = pd.to_numeric(
        subset["mean_alignment"],
        errors="coerce"
    ).dropna()

    if values.empty:
        return np.nan

    return float(values.iloc[0])


# ============================================================
# CHANGE-POINT INFORMATION
# ============================================================

def get_change_point(change_points, pair):

    if change_points.empty:
        return np.nan, np.nan

    subset = change_points[
        change_points["pair"] == pair
    ].copy()

    if subset.empty:
        return np.nan, np.nan

    if "change_magnitude" not in subset.columns:

        return np.nan, np.nan

    subset["change_magnitude"] = pd.to_numeric(
        subset["change_magnitude"],
        errors="coerce"
    )

    subset = subset.dropna(
        subset=["change_magnitude"]
    )

    if subset.empty:
        return np.nan, np.nan

    idx = subset["change_magnitude"].abs().idxmax()

    row = subset.loc[idx]

    year = np.nan

    if "change_year" in row.index:
        year = row["change_year"]

    magnitude = row["change_magnitude"]

    return year, magnitude


# ============================================================
# VALIDATION EVIDENCE
# ============================================================

def get_validation_evidence(
    ground_truth,
    event_detection,
    coverage,
):

    result = {}

    # --------------------------------------------------------
    # Ground-truth validation
    # --------------------------------------------------------

    if not ground_truth.empty:

        result["validation_available"] = True

    else:

        result["validation_available"] = False

    # --------------------------------------------------------
    # Event-conditioned evidence
    # --------------------------------------------------------

    result["event_detection_available"] = (
        not event_detection.empty
    )

    # --------------------------------------------------------
    # Detection coverage
    # --------------------------------------------------------

    result["coverage"] = np.nan

    if not coverage.empty:

        possible_columns = [
            "overall_detection_coverage",
            "detection_coverage",
            "coverage",
        ]

        for column in possible_columns:

            if column in coverage.columns:

                values = pd.to_numeric(
                    coverage[column],
                    errors="coerce"
                ).dropna()

                if not values.empty:

                    result["coverage"] = float(
                        values.iloc[0]
                    )

                    break

    return result


# ============================================================
# BUILD SCORECARD
# ============================================================

def build_scorecard(data):

    summary = normalize_pairs(
        data["summary"]
    )

    temporal = normalize_pairs(
        data["temporal"]
    )

    change_points = normalize_pairs(
        data["change_points"]
    )

    ground_truth = normalize_pairs(
        data["ground_truth"]
    )

    event_detection = normalize_pairs(
        data["event_detection"]
    )

    coverage = normalize_pairs(
        data["coverage"]
    )

    robustness = normalize_pairs(
        data["robustness"]
    )

    rows = []

    if summary.empty:

        raise RuntimeError(
            "country_pair_alignment_summary.csv is required."
        )

    # --------------------------------------------------------
    # Determine country pairs
    # --------------------------------------------------------

    if "pair" in summary.columns:

        pairs = (
            summary["pair"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

    elif (
        "country_a" in summary.columns
        and "country_b" in summary.columns
    ):

        pairs = (
            summary["country_a"].astype(str)
            + "-"
            + summary["country_b"].astype(str)
        ).unique().tolist()

    else:

        raise RuntimeError(
            "Could not identify country pairs."
        )

    # --------------------------------------------------------
    # Build one record per pair
    # --------------------------------------------------------

    for pair in pairs:

        summary_row = summary[
            summary["pair"] == pair
        ]

        if summary_row.empty:
            continue

        summary_row = summary_row.iloc[0]

        historical = get_historical_alignment(
            temporal,
            pair
        )

        recent = get_recent_alignment(
            temporal,
            pair
        )

        # ----------------------------------------------------
        # Calculate temporal change
        # ----------------------------------------------------

        if (
            pd.notna(historical)
            and pd.notna(recent)
        ):

            temporal_change = (
                recent - historical
            )

        else:

            temporal_change = np.nan

        trend = interpret_trend(
            temporal_change
        )

        # ----------------------------------------------------
        # Change point
        # ----------------------------------------------------

        change_year, change_magnitude = (
            get_change_point(
                change_points,
                pair
            )
        )

        # ----------------------------------------------------
        # Validation evidence
        # ----------------------------------------------------

        evidence = get_validation_evidence(
            ground_truth,
            event_detection,
            coverage
        )

        # ----------------------------------------------------
        # Pair-specific validation recall
        # ----------------------------------------------------

        validation_recall = np.nan

        if not ground_truth.empty:

            pair_gt = ground_truth[
                ground_truth["pair"] == pair
            ]

            if (
                not pair_gt.empty
                and "validated_recall" in pair_gt.columns
            ):

                values = pd.to_numeric(
                    pair_gt["validated_recall"],
                    errors="coerce"
                ).dropna()

                if not values.empty:

                    validation_recall = float(
                        values.mean()
                    )

            elif (
                not pair_gt.empty
                and "recall" in pair_gt.columns
            ):

                values = pd.to_numeric(
                    pair_gt["recall"],
                    errors="coerce"
                ).dropna()

                if not values.empty:

                    validation_recall = float(
                        values.mean()
                    )

        # ----------------------------------------------------
        # Robustness
        # ----------------------------------------------------

        robustness_available = (
            not robustness.empty
        )

        confidence = calculate_confidence(
            validation_recall,
            evidence["coverage"],
            robustness_available
        )

        # ----------------------------------------------------
        # Strong trend flag
        # ----------------------------------------------------

        strong_trend = (
            pd.notna(temporal_change)
            and abs(temporal_change)
            >= STRONG_TREND_THRESHOLD
        )

        # ----------------------------------------------------
        # Evidence score
        # ----------------------------------------------------

        evidence_count = 0

        if evidence["validation_available"]:
            evidence_count += 1

        if evidence["event_detection_available"]:
            evidence_count += 1

        if pd.notna(evidence["coverage"]):
            evidence_count += 1

        if robustness_available:
            evidence_count += 1

        if pd.notna(change_magnitude):
            evidence_count += 1

        rows.append(
            {
                "pair": pair,

                "historical_alignment":
                    historical,

                "recent_alignment":
                    recent,

                "temporal_change":
                    temporal_change,

                "interpreted_trend":
                    trend,

                "strong_trend":
                    strong_trend,

                "strongest_change_year":
                    change_year,

                "max_change_magnitude":
                    change_magnitude,

                "validation_recall":
                    validation_recall,

                "detection_coverage":
                    evidence["coverage"],

                "evidence_count":
                    evidence_count,

                "confidence":
                    confidence,

                "validation_available":
                    evidence["validation_available"],

                "event_detection_available":
                    evidence["event_detection_available"],

                "robustness_available":
                    robustness_available,
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# COMPARATIVE SUMMARY
# ============================================================

def print_comparative_summary(scorecard):

    print()
    print("=" * 90)
    print("COMPARATIVE SUMMARY")
    print("=" * 90)

    print()

    print(
        f"Total country pairs: "
        f"{len(scorecard)}"
    )

    print(
        "Improving alignment: "
        f"{(scorecard['interpreted_trend'] == 'IMPROVING').sum()}"
    )

    print(
        "Declining alignment: "
        f"{(scorecard['interpreted_trend'] == 'DECLINING').sum()}"
    )

    print(
        "Stable alignment: "
        f"{(scorecard['interpreted_trend'] == 'STABLE').sum()}"
    )

    print(
        "Insufficient evidence: "
        f"{(scorecard['interpreted_trend'] == 'INSUFFICIENT_EVIDENCE').sum()}"
    )

    print()

    valid_recent = scorecard[
        scorecard["recent_alignment"].notna()
    ]

    if not valid_recent.empty:

        strongest = valid_recent.loc[
            valid_recent["recent_alignment"].idxmax()
        ]

        print(
            "Strongest current pair: "
            f"{strongest['pair']} "
            f"({strongest['recent_alignment']:.3f})"
        )

    improving = scorecard[
        scorecard["interpreted_trend"] == "IMPROVING"
    ]

    if not improving.empty:

        fastest = improving.loc[
            improving["temporal_change"].idxmax()
        ]

        print(
            "Fastest improving pair: "
            f"{fastest['pair']}"
        )

    declining = scorecard[
        scorecard["interpreted_trend"] == "DECLINING"
    ]

    if not declining.empty:

        fastest = declining.loc[
            declining["temporal_change"].idxmin()
        ]

        print(
            "Fastest declining pair: "
            f"{fastest['pair']}"
        )


# ============================================================
# PRINT SCORECARD
# ============================================================

def print_scorecard(scorecard):

    print()
    print("=" * 90)
    print("COUNTRY-PAIR RESULTS")
    print("=" * 90)

    columns = [
        "pair",
        "historical_alignment",
        "recent_alignment",
        "temporal_change",
        "interpreted_trend",
        "strongest_change_year",
        "max_change_magnitude",
        "confidence",
    ]

    display = scorecard[columns].copy()

    print()

    print(
        display.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}"
        )
    )


# ============================================================
# INTERPRETATIONS
# ============================================================

def print_interpretations(scorecard):

    print()
    print("=" * 90)
    print("INTERPRETATIONS")
    print("=" * 90)

    for _, row in scorecard.iterrows():

        pair = row["pair"]

        trend = row["interpreted_trend"]

        confidence = row["confidence"]

        recent = row["recent_alignment"]

        change = row["temporal_change"]

        change_year = row["strongest_change_year"]

        magnitude = row["max_change_magnitude"]

        print()
        print(pair)

        print(
            f"Confidence: {confidence}"
        )

        if pd.isna(recent):

            print(
                f"{pair} does not have sufficient temporal "
                f"alignment measurements for a current interpretation."
            )

            continue

        if trend == "IMPROVING":

            description = (
                "shows increasing alignment "
                "over the observed period"
            )

        elif trend == "DECLINING":

            description = (
                "shows decreasing alignment "
                "over the observed period"
            )

        elif trend == "STABLE":

            description = (
                "shows broadly stable alignment "
                "over the observed period"
            )

        else:

            description = (
                "has insufficient evidence for a "
                "reliable temporal interpretation"
            )

        print(
            f"{pair} {description}. "
            f"Recent alignment is approximately "
            f"{recent:.3f}."
        )

        if pd.notna(change):

            print(
                f"Observed temporal change is "
                f"{change:+.3f}."
            )

        if (
            pd.notna(change_year)
            and pd.notna(magnitude)
        ):

            print(
                f"The strongest detected change occurs "
                f"around {int(change_year)} with magnitude "
                f"{magnitude:.3f}."
            )

        print(
            "This describes temporal association and "
            "voting-alignment patterns; it does not "
            "establish causality."
        )


# ============================================================
# SAVE
# ============================================================

def save_scorecard(scorecard):

    output = (
        BASE_DIR /
        "temporal_country_pair_scorecard.csv"
    )

    scorecard.to_csv(
        output,
        index=False
    )

    print()
    print(
        f"Saved scorecard: {output}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 90)
    print("UN VOTES ANALYZER — COUNTRY-PAIR INTELLIGENCE")
    print("=" * 90)

    data = load_data()

    scorecard = build_scorecard(
        data
    )

    print_comparative_summary(
        scorecard
    )

    print_scorecard(
        scorecard
    )

    print_interpretations(
        scorecard
    )

    save_scorecard(
        scorecard
    )

    print()
    print("=" * 90)
    print(
        "TEMPORAL COUNTRY-PAIR SCORECARD COMPLETE"
    )
    print("=" * 90)


if __name__ == "__main__":
    main()