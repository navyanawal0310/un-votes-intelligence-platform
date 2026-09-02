from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# UN VOTES ANALYZER
# COUNTRY-PAIR COMPARATIVE RANKING
# ============================================================

ROOT = Path.cwd()

INPUT_FILE = ROOT / "country_pair_intelligence.csv"
OUTPUT_FILE = ROOT / "country_pair_rankings.csv"


# ============================================================
# CONFIGURATION
# ============================================================

TOP_N = 10

TREND_THRESHOLD = 0.05

CONFIDENCE_ORDER = {
    "HIGH": 3,
    "MODERATE": 2,
    "LOW": 1,
    "INSUFFICIENT": 0,
}


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Missing required file: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    df.columns = [
        str(c).strip().lower().replace(" ", "_")
        for c in df.columns
    ]

    required = [
        "country_a",
        "country_b",
        "overall_alignment",
        "historical_alignment",
        "recent_alignment",
        "trend",
        "change_point_count",
        "strongest_change_magnitude",
        "confidence",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            "country_pair_intelligence.csv is missing "
            f"required columns: {missing}"
        )

    return df


# ============================================================
# PREPARE DATA
# ============================================================

def prepare_data(df):

    numeric_columns = [
        "overall_alignment",
        "historical_alignment",
        "recent_alignment",
        "change_point_count",
        "strongest_change_magnitude",
        "strongest_effect_size",
    ]

    for column in numeric_columns:

        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    df["alignment_change"] = (
        df["recent_alignment"]
        - df["historical_alignment"]
    )

    # Recalculate trend using the same conservative rule
    # used by the intelligence layer.
    def classify_trend(value):

        if pd.isna(value):
            return "UNKNOWN"

        if value >= TREND_THRESHOLD:
            return "INCREASING"

        if value <= -TREND_THRESHOLD:
            return "DECREASING"

        return "STABLE"

    df["calculated_trend"] = df[
        "alignment_change"
    ].apply(classify_trend)

    df["confidence_rank"] = (
        df["confidence"]
        .astype(str)
        .str.upper()
        .map(CONFIDENCE_ORDER)
        .fillna(0)
    )

    df["pair"] = (
        df["country_a"].astype(str)
        + "-"
        + df["country_b"].astype(str)
    )

    return df


# ============================================================
# 1. STRONGEST CURRENT RELATIONSHIPS
# ============================================================

def strongest_current(df):

    result = (
        df.sort_values(
            "recent_alignment",
            ascending=False,
            na_position="last"
        )
        .head(TOP_N)
        .copy()
    )

    result["rank"] = range(1, len(result) + 1)

    return result[
        [
            "rank",
            "pair",
            "recent_alignment",
            "overall_alignment",
            "trend",
            "confidence",
        ]
    ]


# ============================================================
# 2. FASTEST IMPROVING
# ============================================================

def fastest_improving(df):

    result = (
        df.sort_values(
            "alignment_change",
            ascending=False,
            na_position="last"
        )
        .head(TOP_N)
        .copy()
    )

    result["rank"] = range(1, len(result) + 1)

    return result[
        [
            "rank",
            "pair",
            "historical_alignment",
            "recent_alignment",
            "alignment_change",
            "confidence",
        ]
    ]


# ============================================================
# 3. FASTEST DECLINING
# ============================================================

def fastest_declining(df):

    result = (
        df.sort_values(
            "alignment_change",
            ascending=True,
            na_position="last"
        )
        .head(TOP_N)
        .copy()
    )

    result["rank"] = range(1, len(result) + 1)

    return result[
        [
            "rank",
            "pair",
            "historical_alignment",
            "recent_alignment",
            "alignment_change",
            "confidence",
        ]
    ]


# ============================================================
# 4. MOST TEMPORALLY VOLATILE
# ============================================================

def most_volatile(df):

    result = df.copy()

    # Volatility score is intentionally simple and transparent.
    #
    # Primary component:
    #   strongest detected change magnitude
    #
    # Secondary component:
    #   number of detected change points
    #
    # This avoids creating an opaque statistical volatility metric.

    result["volatility_score"] = (
        result["strongest_change_magnitude"].abs()
        * (
            1
            + np.log1p(
                result["change_point_count"]
            )
        )
    )

    result = (
        result.sort_values(
            "volatility_score",
            ascending=False,
            na_position="last"
        )
        .head(TOP_N)
        .copy()
    )

    result["rank"] = range(1, len(result) + 1)

    return result[
        [
            "rank",
            "pair",
            "change_point_count",
            "strongest_change_magnitude",
            "volatility_score",
            "trend",
            "confidence",
        ]
    ]


# ============================================================
# 5. HIGHEST-CONFIDENCE RELATIONSHIPS
# ============================================================

def highest_confidence(df):

    result = (
        df.sort_values(
            [
                "confidence_rank",
                "recent_alignment",
            ],
            ascending=[
                False,
                False,
            ],
            na_position="last"
        )
        .head(TOP_N)
        .copy()
    )

    result["rank"] = range(1, len(result) + 1)

    return result[
        [
            "rank",
            "pair",
            "confidence",
            "recent_alignment",
            "trend",
            "change_point_count",
        ]
    ]


# ============================================================
# DISPLAY HELPERS
# ============================================================

def print_section(title, df):

    print()
    print("=" * 78)
    print(title)
    print("=" * 78)

    if df.empty:

        print("No results available.")

        return

    print(
        df.to_string(
            index=False
        )
    )


# ============================================================
# BUILD LONG-FORM OUTPUT
# ============================================================

def build_output(
    strongest,
    improving,
    declining,
    volatile,
    confidence,
):

    records = []

    ranking_sets = [
        ("STRONGEST_CURRENT", strongest),
        ("FASTEST_IMPROVING", improving),
        ("FASTEST_DECLINING", declining),
        ("MOST_VOLATILE", volatile),
        ("HIGHEST_CONFIDENCE", confidence),
    ]

    for ranking_name, frame in ranking_sets:

        for _, row in frame.iterrows():

            record = {
                "ranking": ranking_name,
                "rank": row["rank"],
                "pair": row["pair"],
            }

            # Copy all available fields.
            for column in frame.columns:

                if column == "rank":
                    continue

                if column == "pair":
                    continue

                record[column] = row[column]

            records.append(record)

    return pd.DataFrame(records)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 78)
    print("UN VOTES ANALYZER")
    print("COUNTRY-PAIR COMPARATIVE RANKING")
    print("=" * 78)

    df = load_data()

    print()
    print(f"Country pairs loaded: {len(df)}")

    df = prepare_data(df)

    # --------------------------------------------------------
    # RANKINGS
    # --------------------------------------------------------

    strongest = strongest_current(df)

    improving = fastest_improving(
        df[
            df["alignment_change"] > 0
        ]
    )

    declining = fastest_declining(
        df[
            df["alignment_change"] < 0
        ]
    )

    volatile = most_volatile(df)

    confidence = highest_confidence(df)

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    print_section(
        "1. STRONGEST CURRENT RELATIONSHIPS",
        strongest
    )

    print_section(
        "2. FASTEST IMPROVING RELATIONSHIPS",
        improving
    )

    print_section(
        "3. FASTEST DECLINING RELATIONSHIPS",
        declining
    )

    print_section(
        "4. MOST TEMPORALLY VOLATILE RELATIONSHIPS",
        volatile
    )

    print_section(
        "5. HIGHEST-CONFIDENCE RELATIONSHIPS",
        confidence
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 78)
    print("COMPARATIVE SUMMARY")
    print("=" * 78)

    print(
        f"Total country pairs:              {len(df)}"
    )

    print(
        f"Improving relationships:          "
        f"{(df['calculated_trend'] == 'INCREASING').sum()}"
    )

    print(
        f"Declining relationships:          "
        f"{(df['calculated_trend'] == 'DECREASING').sum()}"
    )

    print(
        f"Stable relationships:             "
        f"{(df['calculated_trend'] == 'STABLE').sum()}"
    )

    print(
        f"Unknown relationships:            "
        f"{(df['calculated_trend'] == 'UNKNOWN').sum()}"
    )

    print(
        f"Strongest current pair:           "
        f"{strongest.iloc[0]['pair']}"
        if not strongest.empty
        else "Strongest current pair:           N/A"
    )

    print(
        f"Fastest improving pair:           "
        f"{improving.iloc[0]['pair']}"
        if not improving.empty
        else "Fastest improving pair:           N/A"
    )

    print(
        f"Fastest declining pair:           "
        f"{declining.iloc[0]['pair']}"
        if not declining.empty
        else "Fastest declining pair:           N/A"
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    output = build_output(
        strongest,
        improving,
        declining,
        volatile,
        confidence,
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print("=" * 78)
    print("COUNTRY-PAIR RANKING COMPLETE")
    print("=" * 78)

    print(
        f"Saved rankings: {OUTPUT_FILE.name}"
    )

    print()
    print(
        "Interpretation note:"
    )

    print(
        "Rankings describe observed voting-alignment patterns."
    )

    print(
        "They do not establish political causality."
    )


if __name__ == "__main__":
    main()