"""
UN VOTES ANALYZER
=================

User-facing country-pair intelligence interface.

This module does NOT perform new statistical analysis.

It consumes the canonical analytical pipeline and presents
validated analytical evidence for a selected country pair.
"""

from pathlib import Path
import pandas as pd

from analytical_pipeline import (
    load_pipeline,
    available_pairs,
    get_pair_bundle,
    evidence_status,
)


BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# SAFE VALUE HELPERS
# ============================================================

def safe_float(value):
    """
    Convert a value to float when possible.
    Return None for missing/non-numeric values.
    """

    try:
        value = float(value)

        if pd.isna(value):
            return None

        return value

    except (TypeError, ValueError):
        return None


def format_float(value, digits=3):
    """
    Format numerical values safely.
    """

    value = safe_float(value)

    if value is None:
        return "N/A"

    return f"{value:.{digits}f}"


# ============================================================
# TREND INTERPRETATION
# ============================================================

def interpret_trend(scorecard_row):
    """
    Convert the scorecard trend into user-facing language.
    """

    trend = str(
        scorecard_row.get(
            "interpreted_trend",
            "INSUFFICIENT_EVIDENCE"
        )
    ).upper()

    mapping = {
        "IMPROVING": "increasing",
        "DECLINING": "decreasing",
        "STABLE": "broadly stable",
        "INSUFFICIENT_EVIDENCE": "uncertain",
    }

    return mapping.get(
        trend,
        "uncertain"
    )


# ============================================================
# BUILD RESULT
# ============================================================

def analyze_pair(
    country_a,
    country_b,
    pipeline,
):
    """
    Build a complete country-pair intelligence result.

    The canonical analytical pipeline handles:

        country-pair normalization
        scorecard lookup
        temporal evidence
        change points
        quantitative evaluation
        event analysis
        attribution
        robustness
        null baseline
    """

    bundle = get_pair_bundle(
        pipeline,
        country_a,
        country_b
    )

    scorecard = bundle["scorecard"]

    evidence = evidence_status(
        bundle
    )

    result = {
        "pair": bundle["pair"],

        "pair_key": bundle["pair_key"],

        "historical_alignment":
            scorecard.get(
                "historical_alignment"
            ),

        "recent_alignment":
            scorecard.get(
                "recent_alignment"
            ),

        "temporal_change":
            scorecard.get(
                "temporal_change"
            ),

        "trend":
            interpret_trend(
                scorecard
            ),

        "interpreted_trend":
            scorecard.get(
                "interpreted_trend"
            ),

        "strongest_change_year":
            scorecard.get(
                "strongest_change_year"
            ),

        "max_change_magnitude":
            scorecard.get(
                "max_change_magnitude"
            ),

        "confidence":
            scorecard.get(
                "confidence",
                "UNKNOWN"
            ),

        "validation_recall":
            scorecard.get(
                "validation_recall"
            ),

        "detection_coverage":
            scorecard.get(
                "detection_coverage"
            ),

        "evidence_count":
            scorecard.get(
                "evidence_count",
                0
            ),

        "evidence":
            evidence,

        "bundle":
            bundle,
    }

    return result


# ============================================================
# PRINT EVIDENCE
# ============================================================

def print_evidence(result):

    print()
    print("EVIDENCE")

    for name, available in result["evidence"].items():

        symbol = "✓" if available else "–"

        print(
            f"{symbol} {name}"
        )


# ============================================================
# PRINT RESULT
# ============================================================

def print_result(result):

    print()
    print("=" * 72)
    print("UN VOTES ANALYZER")
    print("=" * 72)

    print()

    print(
        f"COUNTRY PAIR: {result['pair']}"
    )

    print()

    print("CURRENT ALIGNMENT")

    print(
        format_float(
            result["recent_alignment"]
        )
    )

    print()

    print("HISTORICAL ALIGNMENT")

    print(
        format_float(
            result["historical_alignment"]
        )
    )

    print()

    print("TEMPORAL CHANGE")

    change = safe_float(
        result["temporal_change"]
    )

    if change is None:

        print("N/A")

    else:

        print(
            f"{change:+.3f}"
        )

    print()

    print("TREND")

    print(
        result["trend"].upper()
    )

    # --------------------------------------------------------
    # Change point
    # --------------------------------------------------------

    year = safe_float(
        result["strongest_change_year"]
    )

    magnitude = safe_float(
        result["max_change_magnitude"]
    )

    if year is not None:

        print()

        print(
            "STRONGEST DETECTED CHANGE"
        )

        print(
            f"{int(year)}"
        )

        if magnitude is not None:

            print(
                f"Magnitude: {magnitude:.3f}"
            )

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    print()

    print("CONFIDENCE")

    print(
        str(
            result["confidence"]
        ).upper()
    )

    # --------------------------------------------------------
    # Validation metrics
    # --------------------------------------------------------

    recall = safe_float(
        result["validation_recall"]
    )

    coverage = safe_float(
        result["detection_coverage"]
    )

    if recall is not None:

        print()

        print(
            "VALIDATION RECALL"
        )

        print(
            f"{recall:.3f}"
        )

    if coverage is not None:

        print()

        print(
            "DETECTION COVERAGE"
        )

        print(
            f"{coverage:.3f}"
        )

    # --------------------------------------------------------
    # Evidence count
    # --------------------------------------------------------

    print()

    print(
        "EVIDENCE LAYERS"
    )

    print(
        str(
            result["evidence_count"]
        )
    )

    # --------------------------------------------------------
    # Interpretation
    # --------------------------------------------------------

    print()

    print("INTERPRETATION")

    current = safe_float(
        result["recent_alignment"]
    )

    historical = safe_float(
        result["historical_alignment"]
    )

    if (
        current is not None
        and historical is not None
    ):

        print(
            f"{result['pair']} voting alignment "
            f"shows {result['trend']} movement "
            f"over the observed period."
        )

        print(
            f"The current alignment is approximately "
            f"{current:.3f}, compared with historical "
            f"alignment of {historical:.3f}."
        )

    else:

        print(
            f"{result['pair']} does not have sufficient "
            f"alignment measurements for a complete "
            f"temporal interpretation."
        )

    print()

    print(
        "This describes observed UN voting-alignment "
        "patterns; it does not establish political "
        "intent, diplomatic motivation, or causality."
    )

    # --------------------------------------------------------
    # Evidence
    # --------------------------------------------------------

    print_evidence(
        result
    )

    print()

    print("=" * 72)


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "Loading validated analytical pipeline..."
    )

    try:

        pipeline = load_pipeline()

    except Exception as error:

        print()
        print(
            f"ERROR loading analytical pipeline: {error}"
        )

        return

    # --------------------------------------------------------
    # Pipeline status
    # --------------------------------------------------------

    print()

    print(
        "Available country pairs:"
    )

    pairs = available_pairs(
        pipeline
    )

    if not pairs:

        print(
            "  No country pairs available."
        )

        return

    for pair in pairs:

        print(
            f"  {pair}"
        )

    print()

    # --------------------------------------------------------
    # User input
    # --------------------------------------------------------

    country_a = input(
        "Enter first country code: "
    )

    country_b = input(
        "Enter second country code: "
    )

    # --------------------------------------------------------
    # Analysis
    # --------------------------------------------------------

    try:

        result = analyze_pair(
            country_a,
            country_b,
            pipeline
        )

        print_result(
            result
        )

    except ValueError as error:

        print()

        print(
            f"ERROR: {error}"
        )

    except Exception as error:

        print()

        print(
            "UNEXPECTED PIPELINE ERROR:"
        )

        print(
            f"{type(error).__name__}: {error}"
        )


if __name__ == "__main__":
    main()