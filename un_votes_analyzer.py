"""
UN VOTES ANALYZER
=================

Final user-facing analytical layer.

This module consolidates previously validated analytical
outputs into a simple country-pair intelligence interface.

It does NOT perform new statistical analysis.
It does NOT establish causality.
It translates existing validated measurements into
structured, interpretable results.
"""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

SCORECARD_FILE = BASE_DIR / "temporal_country_pair_scorecard.csv"
TEMPORAL_FILE = BASE_DIR / "country_pair_temporal_alignment.csv"
CHANGE_POINT_FILE = BASE_DIR / "temporal_alignment_change_points.csv"
EVENT_FILE = BASE_DIR / "temporal_event_conditioned_detection.csv"
ROBUSTNESS_FILE = BASE_DIR / "temporal_robustness_analysis.csv"
NULL_FILE = BASE_DIR / "temporal_null_baseline.csv"


def load_data():
    return {
        "scorecard": pd.read_csv(SCORECARD_FILE),
        "temporal": pd.read_csv(TEMPORAL_FILE),
        "change_points": pd.read_csv(CHANGE_POINT_FILE),
        "event": pd.read_csv(EVENT_FILE),
        "robustness": pd.read_csv(ROBUSTNESS_FILE),
        "null": pd.read_csv(NULL_FILE),
    }


def normalize_country_code(country):
    """Normalize user input without imposing pair orientation."""
    return str(country).upper().strip()


def find_pair(scorecard, country_a, country_b):
    """
    Find a country pair regardless of input order.

    The scorecard has its own canonical orientation, e.g.
    IND-CHN and USA-RUS. It is therefore incorrect to assume
    alphabetical ordering when constructing the lookup key.
    """
    country_a = normalize_country_code(country_a)
    country_b = normalize_country_code(country_b)

    if not country_a or not country_b or country_a == country_b:
        return None

    pairs = (
        scorecard["pair"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    forward = f"{country_a}-{country_b}"
    reverse = f"{country_b}-{country_a}"

    matches = scorecard[pairs.isin([forward, reverse])]

    if matches.empty:
        return None

    return matches.iloc[0]


def interpret_trend(row):
    trend = str(row.get("interpreted_trend", "")).upper()

    if trend == "IMPROVING":
        return "increasing"
    if trend == "DECLINING":
        return "decreasing"
    if trend == "STABLE":
        return "broadly stable"

    return "uncertain"


def evidence_status(data):
    return {
        "Temporal alignment": not data["temporal"].empty,
        "Change-point analysis": not data["change_points"].empty,
        "Event-conditioned analysis": not data["event"].empty,
        "Robustness analysis": not data["robustness"].empty,
        "Null baseline": not data["null"].empty,
    }


def analyze_pair(country_a, country_b, data):
    country_a = normalize_country_code(country_a)
    country_b = normalize_country_code(country_b)

    row = find_pair(
        data["scorecard"],
        country_a,
        country_b,
    )

    if row is None:
        raise ValueError(
            f"No analytical result found for {country_a}-{country_b}"
        )

    # Always display the pair using the scorecard's canonical orientation.
    pair = str(row["pair"]).upper().strip()

    return {
        "pair": pair,
        "historical_alignment": row.get("historical_alignment"),
        "recent_alignment": row.get("recent_alignment"),
        "temporal_change": row.get("temporal_change"),
        "trend": interpret_trend(row),
        "strongest_change_year": row.get("strongest_change_year"),
        "max_change_magnitude": row.get("max_change_magnitude"),
        "confidence": row.get("confidence", "MODERATE"),
        "evidence": evidence_status(data),
    }


def print_result(result):
    print()
    print("=" * 64)
    print("UN VOTES ANALYZER")
    print("=" * 64)
    print()
    print(f"COUNTRY PAIR: {result['pair']}")

    print()
    print("CURRENT ALIGNMENT")
    print(f"{result['recent_alignment']:.3f}")

    print()
    print("HISTORICAL ALIGNMENT")
    print(f"{result['historical_alignment']:.3f}")

    print()
    print("TEMPORAL CHANGE")
    print(f"{result['temporal_change']:+.3f}")

    print()
    print("TREND")
    print(result["trend"].upper())

    if pd.notna(result["strongest_change_year"]):
        print()
        print("STRONGEST DETECTED CHANGE")
        print(f"{int(result['strongest_change_year'])}")

        if pd.notna(result["max_change_magnitude"]):
            print(
                "Magnitude: "
                f"{result['max_change_magnitude']:.3f}"
            )

    print()
    print("CONFIDENCE")
    print(result["confidence"])

    print()
    print("INTERPRETATION")
    print(
        f"{result['pair']} voting alignment shows "
        f"{result['trend']} movement over the observed period."
    )
    print(
        f"The current alignment is approximately "
        f"{result['recent_alignment']:.3f}, compared with "
        f"historical alignment of "
        f"{result['historical_alignment']:.3f}."
    )
    print(
        "This describes observed UN voting-alignment patterns; "
        "it does not establish political intent, diplomatic "
        "motivation, or causality."
    )

    print()
    print("EVIDENCE")
    for name, available in result["evidence"].items():
        symbol = "✓" if available else "–"
        print(f"{symbol} {name}")

    print()
    print("=" * 64)


def main():
    print("Loading validated analytical outputs...")
    data = load_data()

    print("Available country pairs:")
    pairs = sorted(
        data["scorecard"]["pair"]
        .dropna()
        .astype(str)
        .unique()
    )

    for pair in pairs:
        print(f"  {pair}")

    print()

    country_a = input("Enter first country code: ")
    country_b = input("Enter second country code: ")

    try:
        result = analyze_pair(country_a, country_b, data)
        print_result(result)
    except ValueError as error:
        print()
        print(f"ERROR: {error}")


if __name__ == "__main__":
    main()
