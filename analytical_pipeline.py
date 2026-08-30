"""
UN VOTES ANALYZER
ANALYTICAL DATA PIPELINE
========================

Purpose
-------
Connect all validated analytical outputs into one canonical
data pipeline.

This module does NOT perform new statistical analysis.

It provides:
    RAW / DERIVED CSV
        ↓
    DATA LOADING
        ↓
    NORMALIZATION
        ↓
    COUNTRY-PAIR BUNDLING
        ↓
    UNIFIED ANALYTICAL DATA

All downstream intelligence modules should consume this
pipeline instead of independently loading CSV files.
"""

from pathlib import Path
import pandas as pd


# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# ANALYTICAL DATA SOURCES
# ============================================================

DATA_SOURCES = {
    "scorecard": "temporal_country_pair_scorecard.csv",

    "temporal_alignment":
        "country_pair_temporal_alignment.csv",

    "change_points":
        "temporal_alignment_change_points.csv",
    
    "relationship_state":
    "data/gold/analytical/country_pair_relationships.parquet",

    "ground_truth":
        "temporal_ground_truth.csv",

    "ground_truth_validation":
        "temporal_ground_truth_validation.csv",

    "quantitative_evaluation":
        "temporal_quantitative_evaluation.csv",

    "quantitative_by_pair":
        "temporal_quantitative_by_pair.csv",

    "event_conditioned":
        "temporal_event_conditioned_detection.csv",

    "event_signal":
        "temporal_event_signal_diagnostic.csv",

    "detection_coverage":
        "temporal_detection_coverage.csv",

    "robustness":
        "temporal_robustness_analysis.csv",

    "null_baseline":
        "temporal_null_baseline.csv",

    "issue_attribution":
        "change_point_explanations.csv",

    "episode_attribution":
        "temporal_issue_episode_attribution.csv",

    "attribution_robustness":
        "temporal_issue_attribution_robustness.csv",

    "attribution_robustness_summary":
        "temporal_issue_attribution_robustness_summary.csv",
}


# ============================================================
# OPTIONAL DATA SOURCES
# ============================================================

OPTIONAL_SOURCES = {
    "ground_truth": True,
    "ground_truth_validation": True,
    "quantitative_evaluation": True,
    "quantitative_by_pair": True,
    "event_conditioned": True,
    "event_signal": True,
    "detection_coverage": True,
    "robustness": True,
    "null_baseline": True,
    "issue_attribution": True,
    "episode_attribution": True,
    "attribution_robustness": True,
    "attribution_robustness_summary": True,
}


# ============================================================
# PAIR NORMALIZATION
# ============================================================

def normalize_country(country):
    """
    Normalize a country code.
    """

    return str(country).upper().strip()


def normalize_pair(country_a, country_b):
    """
    Create an orientation-independent country-pair key.

    Example:

        IND + CHN -> CHN-IND
        CHN + IND -> CHN-IND

    This key is used ONLY for matching.

    It is NOT used as the display/canonical pair name.
    """

    countries = sorted(
        [
            normalize_country(country_a),
            normalize_country(country_b),
        ]
    )

    return f"{countries[0]}-{countries[1]}"


def add_pair_column(df):
    """
    Add a canonical matching key to country-pair data.

    The original country_a / country_b columns are preserved.

    The generated 'pair_key' is orientation-independent.

    Example:

        IND + CHN -> CHN-IND
        CHN + IND -> CHN-IND
    """

    df = df.copy()

    if (
        "country_a" in df.columns
        and "country_b" in df.columns
    ):

        df["country_a"] = (
            df["country_a"]
            .astype(str)
            .str.upper()
            .str.strip()
        )

        df["country_b"] = (
            df["country_b"]
            .astype(str)
            .str.upper()
            .str.strip()
        )

        df["pair_key"] = [
            normalize_pair(a, b)
            for a, b in zip(
                df["country_a"],
                df["country_b"]
            )
        ]

    elif "pair" in df.columns:

        df["pair"] = (
            df["pair"]
            .astype(str)
            .str.upper()
            .str.strip()
        )

        pair_keys = []

        for value in df["pair"]:

            parts = str(value).split("-")

            if len(parts) == 2:

                pair_keys.append(
                    normalize_pair(
                        parts[0],
                        parts[1]
                    )
                )

            else:

                pair_keys.append(
                    str(value).upper().strip()
                )

        df["pair_key"] = pair_keys

    return df



# ============================================================
# LOAD SINGLE FILE
# ============================================================

def load_data(filename, required=False):
    """
    Load an analytical data source.

    Supports CSV and Parquet while keeping the
    analytical pipeline source-agnostic.
    """

    path = BASE_DIR / filename

    if not path.exists():

        if required:
            raise FileNotFoundError(
                f"Required analytical file missing: {path}"
            )

        return pd.DataFrame()

    try:

        if path.suffix.lower() == ".parquet":
            df = pd.read_parquet(path)

        else:
            df = pd.read_csv(path)

    except Exception as error:

        raise RuntimeError(
            f"Could not read analytical file: "
            f"{path}\n{error}"
        )

    return add_pair_column(df)

# ============================================================
# LOAD COMPLETE PIPELINE
# ============================================================

def load_pipeline():
    """
    Load all analytical outputs into one dictionary.
    """

    pipeline = {}

    for name, filename in DATA_SOURCES.items():

        required = (
            name == "scorecard"
        )

        df = load_data(
            filename,
            required=required
        )

        pipeline[name] = df

    return pipeline


# ============================================================
# PIPELINE STATUS
# ============================================================

def pipeline_status(pipeline):
    """
    Produce a machine-readable status table showing
    which analytical layers are available.
    """

    rows = []

    for name, df in pipeline.items():

        rows.append(
            {
                "layer": name,
                "rows": len(df),
                "available": not df.empty,
                "columns": len(df.columns),
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# GET AVAILABLE COUNTRY PAIRS
# ============================================================

def available_pairs(pipeline):
    """
    Return all globally available country pairs.

    Relationship state defines the analytical pair universe.
    The scorecard is only a derived/benchmark layer.
    """

    relationship_state = pipeline.get(
        "relationship_state",
        pd.DataFrame()
    )

    if not relationship_state.empty:

        relationship_state = add_pair_column(
            relationship_state
        )

        return sorted(
            relationship_state["pair_key"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

    # Fallback for older pipeline states

    scorecard = pipeline.get(
        "scorecard",
        pd.DataFrame()
    )

    if scorecard.empty:
        return []

    if "pair" not in scorecard.columns:
        return []

    return sorted(
        scorecard["pair"]
        .dropna()
        .astype(str)
        .str.upper()
        .str.strip()
        .unique()
        .tolist()
    )

def available_countries(pipeline):
    """
    Return all countries represented in the analytical
    relationship-state universe.
    """

    relationship_state = pipeline.get(
        "relationship_state",
        pd.DataFrame()
    )

    if relationship_state.empty:
        return []

    countries = set()

    for column in ("country_a", "country_b"):
        if column in relationship_state.columns:
            countries.update(
                relationship_state[column]
                .dropna()
                .astype(str)
                .str.upper()
                .str.strip()
                .tolist()
            )

    return sorted(countries)

# ============================================================
# FIND SCORECARD ROW
# ============================================================
def find_scorecard_row(pipeline, pair):
    """
    Find a scorecard record using an orientation-independent
    country-pair key.
    """

    scorecard = pipeline["scorecard"]

    if scorecard.empty:
        return None

    scorecard = add_pair_column(
        scorecard
    )

    matches = scorecard[
        scorecard["pair_key"] == pair
    ]

    if matches.empty:
        return None

    return matches.iloc[0]



# ============================================================
# FILTER DATA BY PAIR
# ============================================================

def filter_pair(df, pair):
    """
    Return all rows belonging to a country pair.

    Matching is orientation-independent.

    The original country ordering in the source data
    is preserved.
    """

    if df.empty:
        return df.copy()

    df = add_pair_column(
        df
    )

    if "pair_key" not in df.columns:
        return pd.DataFrame()

    return df[
        df["pair_key"] == pair
    ].copy()

# ============================================================
# BUILD COUNTRY-PAIR BUNDLE
# ============================================================

def get_pair_bundle(
    pipeline,
    country_a,
    country_b
):
    """
    Build the complete analytical evidence bundle
    for one country pair.

    Country-pair availability is determined by the
    global analytical layers, not by the benchmark
    scorecard.

    User input can be in either order:

        IND + CHN
        CHN + IND

    Both resolve to the same pair_key.
    """

    pair_key = normalize_pair(
        country_a,
        country_b
    )

    # --------------------------------------------------------
    # Determine whether this pair exists globally
    # --------------------------------------------------------

    relationship_state = pipeline.get(
        "relationship_state",
        pd.DataFrame()
    )

    if relationship_state.empty:
        raise ValueError(
            "Relationship-state layer is unavailable."
        )

    relationship_state = add_pair_column(
        relationship_state
    )

    pair_relationship = relationship_state[
        relationship_state["pair_key"] == pair_key
    ].copy()

    if pair_relationship.empty:
        raise ValueError(
            f"No analytical result found for "
            f"{country_a}-{country_b}"
        )

    # --------------------------------------------------------
    # Scorecard is optional evidence
    # --------------------------------------------------------

    scorecard_row = find_scorecard_row(
        pipeline,
        pair_key
    )

    if scorecard_row is not None:
        canonical_pair = str(
            scorecard_row["pair"]
        ).upper().strip()
    else:
        canonical_pair = pair_key

    # --------------------------------------------------------
    # Build complete analytical bundle
    # --------------------------------------------------------

    bundle = {
        "pair": canonical_pair,

        "pair_key": pair_key,

        "scorecard": (
            scorecard_row
            if scorecard_row is not None
            else None
        ),

        "relationship_state":
            pair_relationship,

        "temporal_alignment":
            filter_pair(
                pipeline["temporal_alignment"],
                pair_key
            ),

        "change_points":
            filter_pair(
                pipeline["change_points"],
                pair_key
            ),

        "quantitative":
            filter_pair(
                pipeline["quantitative_by_pair"],
                pair_key
            ),

        "event_conditioned":
            filter_pair(
                pipeline["event_conditioned"],
                pair_key
            ),

        "event_signal":
            filter_pair(
                pipeline["event_signal"],
                pair_key
            ),

        "detection_coverage":
            filter_pair(
                pipeline["detection_coverage"],
                pair_key
            ),

        "issue_attribution":
            filter_pair(
                pipeline["issue_attribution"],
                pair_key
            ),

        "episode_attribution":
            filter_pair(
                pipeline["episode_attribution"],
                pair_key
            ),

        "attribution_robustness":
            filter_pair(
                pipeline["attribution_robustness"],
                pair_key
            ),

        "robustness":
            filter_pair(
                pipeline["robustness"],
                pair_key
            ),

        "null_baseline":
            pipeline["null_baseline"],
    }

    return bundle

# ============================================================
# EVIDENCE AVAILABILITY
# ============================================================

def evidence_status(bundle):
    """
    Determine which analytical evidence layers are available
    for a country pair.
    """

    checks = {}

    checks["Temporal alignment"] = (
        not bundle["temporal_alignment"].empty
    )
    checks["Relationship state"] = (
        not bundle["relationship_state"].empty
    )
    checks["Change-point analysis"] = (
        not bundle["change_points"].empty
    )

    checks["Quantitative evaluation"] = (
        not bundle["quantitative"].empty
    )

    checks["Event-conditioned analysis"] = (
        not bundle["event_conditioned"].empty
    )

    checks["Event signal diagnostics"] = (
        not bundle["event_signal"].empty
    )

    checks["Detection coverage"] = (
        not bundle["detection_coverage"].empty
    )

    checks["Issue attribution"] = (
        not bundle["issue_attribution"].empty
    )

    checks["Episode attribution"] = (
        not bundle["episode_attribution"].empty
    )

    checks["Attribution robustness"] = (
        not bundle["attribution_robustness"].empty
    )

    checks["Temporal robustness"] = (
        not bundle["robustness"].empty
    )

    checks["Null baseline"] = (
        not bundle["null_baseline"].empty
    )

    return checks


# ============================================================
# PIPELINE DIAGNOSTIC
# ============================================================

def print_pipeline_status(pipeline):
    """
    Print a concise pipeline diagnostic.
    """

    print()
    print("=" * 72)
    print("UN VOTES ANALYZER — DATA PIPELINE")
    print("=" * 72)

    print()

    status = pipeline_status(
        pipeline
    )

    for _, row in status.iterrows():

        symbol = (
            "[OK]"
            if row["available"]
            else "[--]"
        )

        print(
            f"{symbol} "
            f"{row['layer']:<38} "
            f"{row['rows']:>6} rows"
        )

    print()

    pairs = available_pairs(
        pipeline
    )

    print(
        f"Available country pairs: {len(pairs)}"
    )

    print(
        f"[OK] Available country pairs: {len(pairs):,}"
    )

    print(
        "[OK] Pair universe is global; "
        "individual pairs can be queried on demand."
    )

    print(
        "[OK] Sample pairs:"
    )

    for pair in pairs[:10]:
        print(f"     {pair}")

    print()

    print("=" * 72)


# ============================================================
# MAIN DIAGNOSTIC
# ============================================================

def main():

    print(
        "Loading analytical pipeline..."
    )

    pipeline = load_pipeline()

    print_pipeline_status(
        pipeline
    )


if __name__ == "__main__":
    main()