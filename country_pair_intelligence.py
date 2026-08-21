"""
UN VOTES ANALYZER
COUNTRY-PAIR INTELLIGENCE REPORT

Purpose
-------
Convert the validated country-pair scorecard into a concise,
human-readable intelligence layer.

This module does NOT create new statistical measurements.

It interprets previously calculated temporal alignment evidence.

Important:
    Voting alignment is descriptive.
    It does not establish political intent, alliance, causality,
    or diplomatic motivation.
"""

from pathlib import Path
import pandas as pd
import numpy as np


BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = (
    BASE_DIR /
    "temporal_country_pair_scorecard.csv"
)

OUTPUT_FILE = (
    BASE_DIR /
    "temporal_country_pair_intelligence.csv"
)


# ============================================================
# INTERPRETATION
# ============================================================

def build_interpretation(row):

    pair = row["pair"]

    trend = row["interpreted_trend"]

    current = row["recent_alignment"]

    historical = row["historical_alignment"]

    change = row["temporal_change"]

    confidence = row["confidence"]

    # --------------------------------------------------------
    # Insufficient evidence
    # --------------------------------------------------------

    if trend == "INSUFFICIENT_EVIDENCE":

        return (
            f"{pair} does not have sufficient temporal "
            f"alignment evidence for a reliable trend "
            f"interpretation."
        )

    # --------------------------------------------------------
    # Stable
    # --------------------------------------------------------

    if trend == "STABLE":

        return (
            f"{pair} shows broadly stable voting alignment "
            f"over the observed period. Current alignment is "
            f"approximately {current:.3f}. The observed movement "
            f"from the historical level is small ({change:+.3f})."
        )

    # --------------------------------------------------------
    # Improving
    # --------------------------------------------------------

    if trend == "IMPROVING":

        return (
            f"{pair} shows increasing voting alignment over "
            f"the observed period. Alignment moved from "
            f"{historical:.3f} historically to approximately "
            f"{current:.3f} recently, a change of "
            f"{change:+.3f}."
        )

    # --------------------------------------------------------
    # Declining
    # --------------------------------------------------------

    if trend == "DECLINING":

        return (
            f"{pair} shows decreasing voting alignment over "
            f"the observed period. Alignment moved from "
            f"{historical:.3f} historically to approximately "
            f"{current:.3f} recently, a change of "
            f"{change:+.3f}."
        )

    return (
        f"{pair} has no reliable temporal interpretation."
    )


# ============================================================
# EVIDENCE LEVEL
# ============================================================

def classify_evidence(row):

    evidence_count = row.get(
        "evidence_count",
        0
    )

    robustness = row.get(
        "robustness_available",
        False
    )

    validation = row.get(
        "validation_available",
        False
    )

    if evidence_count >= 4 and robustness and validation:

        return "STRONG"

    if evidence_count >= 2:

        return "MODERATE"

    return "LIMITED"


# ============================================================
# CAUTION
# ============================================================

def build_caution(row):

    trend = row["interpreted_trend"]

    confidence = row["confidence"]

    evidence = row["evidence_level"]

    if trend == "INSUFFICIENT_EVIDENCE":

        return (
            "Insufficient evidence for a substantive "
            "temporal interpretation."
        )

    if confidence == "LOW":

        return (
            "Interpretation should be treated cautiously "
            "because supporting validation evidence is limited."
        )

    if evidence == "LIMITED":

        return (
            "Interpretation is descriptive and should not "
            "be treated as evidence of political intent."
        )

    return (
        "Voting alignment describes observed voting patterns; "
        "it does not establish causality, political intent, "
        "or diplomatic motivation."
    )


# ============================================================
# BUILD REPORT
# ============================================================

def build_report(df):

    rows = []

    for _, row in df.iterrows():

        current = row["recent_alignment"]

        historical = row["historical_alignment"]

        change = row["temporal_change"]

        # ----------------------------------------------------
        # Evidence
        # ----------------------------------------------------

        evidence_count = row.get(
            "evidence_count",
            0
        )

        # ----------------------------------------------------
        # Evidence level
        # ----------------------------------------------------

        evidence_level = classify_evidence(
            row
        )

        # ----------------------------------------------------
        # Interpretation
        # ----------------------------------------------------

        interpretation = build_interpretation(
            row
        )

        # ----------------------------------------------------
        # Caution
        # ----------------------------------------------------

        # Temporarily create a copy-like dictionary
        # for the caution function.

        temp = row.copy()

        temp["evidence_level"] = (
            evidence_level
        )

        caution = build_caution(
            temp
        )

        # ----------------------------------------------------
        # Change point
        # ----------------------------------------------------

        change_year = row.get(
            "strongest_change_year",
            np.nan
        )

        change_magnitude = row.get(
            "max_change_magnitude",
            np.nan
        )

        rows.append(
            {
                "pair": row["pair"],

                "historical_alignment":
                    historical,

                "current_alignment":
                    current,

                "temporal_change":
                    change,

                "trend":
                    row["interpreted_trend"],

                "confidence":
                    row["confidence"],

                "evidence_level":
                    evidence_level,

                "evidence_count":
                    evidence_count,

                "key_change_year":
                    change_year,

                "key_change_magnitude":
                    change_magnitude,

                "interpretation":
                    interpretation,

                "caution":
                    caution,
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# PRINT REPORT
# ============================================================

def print_report(df):

    print()
    print("=" * 100)
    print("UN VOTES ANALYZER — COUNTRY-PAIR INTELLIGENCE")
    print("=" * 100)

    print()

    print(
        f"Country pairs evaluated: {len(df)}"
    )

    print()

    print(
        "Trend distribution:"
    )

    print(
        df["trend"]
        .value_counts()
        .to_string()
    )

    print()

    print(
        "Confidence distribution:"
    )

    print(
        df["confidence"]
        .value_counts()
        .to_string()
    )

    print()
    print("=" * 100)
    print("COUNTRY-PAIR INTELLIGENCE")
    print("=" * 100)

    for _, row in df.iterrows():

        print()
        print(
            f"{row['pair']}"
        )

        print(
            f"Trend:              "
            f"{row['trend']}"
        )

        print(
            f"Current alignment:  "
            f"{row['current_alignment']:.3f}"
        )

        print(
            f"Historical level:   "
            f"{row['historical_alignment']:.3f}"
        )

        print(
            f"Temporal change:    "
            f"{row['temporal_change']:+.3f}"
        )

        print(
            f"Confidence:         "
            f"{row['confidence']}"
        )

        print(
            f"Evidence level:     "
            f"{row['evidence_level']}"
        )

        if pd.notna(
            row["key_change_year"]
        ):

            print(
                f"Key change year:    "
                f"{int(row['key_change_year'])}"
            )

        print(
            f"Interpretation:     "
            f"{row['interpretation']}"
        )

        print(
            f"Caution:            "
            f"{row['caution']}"
        )


# ============================================================
# COMPARATIVE INTELLIGENCE
# ============================================================

def print_comparative_intelligence(df):

    print()
    print("=" * 100)
    print("COMPARATIVE INTELLIGENCE")
    print("=" * 100)

    valid = df[
        df["current_alignment"].notna()
    ]

    if valid.empty:
        return

    # --------------------------------------------------------
    # Strongest current alignment
    # --------------------------------------------------------

    strongest = valid.loc[
        valid["current_alignment"].idxmax()
    ]

    print()

    print(
        "Strongest current alignment:"
    )

    print(
        f"  {strongest['pair']} "
        f"({strongest['current_alignment']:.3f})"
    )

    # --------------------------------------------------------
    # Largest improvement
    # --------------------------------------------------------

    improving = valid[
        valid["trend"] == "IMPROVING"
    ]

    if not improving.empty:

        row = improving.loc[
            improving["temporal_change"].idxmax()
        ]

        print()

        print(
            "Largest observed improvement:"
        )

        print(
            f"  {row['pair']} "
            f"({row['temporal_change']:+.3f})"
        )

    # --------------------------------------------------------
    # Largest decline
    # --------------------------------------------------------

    declining = valid[
        valid["trend"] == "DECLINING"
    ]

    if not declining.empty:

        row = declining.loc[
            declining["temporal_change"].idxmin()
        ]

        print()

        print(
            "Largest observed decline:"
        )

        print(
            f"  {row['pair']} "
            f"({row['temporal_change']:+.3f})"
        )

    # --------------------------------------------------------
    # Stable relationships
    # --------------------------------------------------------

    stable = valid[
        valid["trend"] == "STABLE"
    ]

    if not stable.empty:

        print()

        print(
            "Stable relationship(s):"
        )

        for pair in stable["pair"]:

            print(
                f"  {pair}"
            )


# ============================================================
# SAVE
# ============================================================

def save_report(df):

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()

    print(
        f"Saved intelligence report: "
        f"{OUTPUT_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "Loading validated country-pair scorecard..."
    )

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Missing required input: {INPUT_FILE}"
        )

    scorecard = pd.read_csv(
        INPUT_FILE
    )

    report = build_report(
        scorecard
    )

    print_report(
        report
    )

    print_comparative_intelligence(
        report
    )

    save_report(
        report
    )

    print()
    print("=" * 100)
    print(
        "COUNTRY-PAIR INTELLIGENCE COMPLETE"
    )
    print("=" * 100)


if __name__ == "__main__":
    main()