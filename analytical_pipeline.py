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
from functools import lru_cache
import duckdb
import pandas as pd
from packages.analytics.temporal_change_episodes import (
    build_change_episodes,
)


# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# ANALYTICAL DATA SOURCES
# ============================================================

DATA_SOURCES = {
    "scorecard":
        "reports/analytical_outputs/temporal_country_pair_scorecard.csv",

    "temporal_alignment":
        "reports/analytical_outputs/country_pair_temporal_alignment.csv",

    "change_points":
        "reports/analytical_outputs/temporal_alignment_change_points.csv",
    
    "relationship_state":
    "data/gold/analytical/country_pair_relationships.parquet",

    "ground_truth":
    "reports/analytical_outputs/temporal_ground_truth.csv",

    "ground_truth_validation":
        "reports/analytical_outputs/temporal_ground_truth_validation.csv",

    "quantitative_evaluation":
        "reports/analytical_outputs/temporal_quantitative_evaluation.csv",

    "quantitative_by_pair":
        "reports/analytical_outputs/temporal_quantitative_by_pair.csv",

    "event_conditioned":
        "reports/analytical_outputs/temporal_event_conditioned_detection.csv",

    "event_signal":
        "reports/analytical_outputs/temporal_event_signal_diagnostic.csv",

    "detection_coverage":
        "reports/analytical_outputs/temporal_detection_coverage.csv",

    "robustness":
        "reports/analytical_outputs/temporal_robustness_analysis.csv",

    "null_baseline":
        "reports/analytical_outputs/temporal_null_baseline.csv",

    "issue_attribution":
        "reports/analytical_outputs/change_point_explanations.csv",

    "episode_attribution":
        "reports/analytical_outputs/temporal_issue_episode_attribution.csv",

    "attribution_robustness":
        "reports/analytical_outputs/temporal_issue_attribution_robustness.csv",

    "attribution_robustness_summary":
        "reports/analytical_outputs/temporal_issue_attribution_robustness_summary.csv",
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
    if "pair_key" in df.columns:
        return df

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
# RELATIONSHIP-STATE ACCESS
# ============================================================

def _relationship_state_path():
    """
    Return the relationship-state Parquet path.

    The relationship-state layer is intentionally queried lazily.
    It is large (~937k rows) and should not be materialized into
    pandas for every API process/request.
    """

    path = BASE_DIR / DATA_SOURCES["relationship_state"]

    if not path.exists():
        raise FileNotFoundError(
            f"Required analytical file missing: {path}"
        )

    return path


def _query_relationship_state(pair_key=None):
    """
    Query relationship-state Parquet directly with DuckDB.

    When pair_key is supplied, only that country's pair history
    is materialized into pandas. This avoids loading the complete
    relationship-state table into memory.
    """

    path = _relationship_state_path()
    parquet = str(path).replace("'", "''")

    con = duckdb.connect()
    try:
        if pair_key is None:
            sql = f"""
                SELECT DISTINCT
                    UPPER(TRIM(country_a)) AS country_a,
                    UPPER(TRIM(country_b)) AS country_b,
                    UPPER(TRIM(country_a)) || '-' ||
                    UPPER(TRIM(country_b)) AS pair_key
                FROM read_parquet('{parquet}')
            """
            return con.execute(sql).fetchdf()

        parts = str(pair_key).split("-", 1)

        if len(parts) != 2:
            return pd.DataFrame()

        country_a, country_b = parts

        sql = f"""
            SELECT
                country_a,
                country_b,
                year,
                relationship_score,
                relationship_direction,
                mean_alignment,
                mean_divergence,
                directional_agreement,
                evidence_count,
                change_episode_count,
                confirmed_episode_count,
                evidence_source,
                provenance,
                ? AS pair_key
            FROM read_parquet('{parquet}')
            WHERE
                (
                    UPPER(TRIM(country_a)) = ?
                    AND UPPER(TRIM(country_b)) = ?
                )
                OR
                (
                    UPPER(TRIM(country_a)) = ?
                    AND UPPER(TRIM(country_b)) = ?
                )
            ORDER BY year
        """

        return con.execute(
            sql,
            [
                pair_key,
                country_a,
                country_b,
                country_b,
                country_a,
            ],
        ).fetchdf()

    finally:
        con.close()


# ============================================================
# LOAD COMPLETE PIPELINE
# ============================================================
@lru_cache(maxsize=1)
def load_pipeline():
    """
    Load the smaller analytical outputs into one dictionary.

    The large relationship-state Parquet layer is deliberately
    excluded from eager pandas loading and is queried on demand.
    """

    pipeline = {}

    for name, filename in DATA_SOURCES.items():

        if name == "relationship_state":
            continue

        required = (
            name == "scorecard"
        )

        df = load_data(
            filename,
            required=required
        )

        pipeline[name] = df

    # Marker retained for compatibility with callers that inspect
    # the pipeline dictionary. The actual data is loaded lazily.
    pipeline["relationship_state"] = pd.DataFrame()

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

    Relationship state defines the analytical pair universe,
    but it is queried lazily so the 937k-row Parquet file is
    never materialized into pandas.
    """

    try:
        relationship_pairs = _query_relationship_state()

        if not relationship_pairs.empty:
            pairs = []
            for a, b in zip(
                relationship_pairs["country_a"],
                relationship_pairs["country_b"],
            ):
                pairs.append(
                    normalize_pair(a, b)
                )

            return sorted(set(pairs))

    except FileNotFoundError:
        pass

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

    The Parquet source is queried directly so the complete
    relationship-state table is never loaded into pandas.
    """

    try:
        relationship_state = _query_relationship_state()

        if not relationship_state.empty:
            countries = set()

            for column in ("country_a", "country_b"):
                countries.update(
                    relationship_state[column]
                    .dropna()
                    .astype(str)
                    .str.upper()
                    .str.strip()
                    .tolist()
                )

            return sorted(countries)

    except FileNotFoundError:
        pass

    return []

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

    Uses the precomputed pair_key when available.
    This avoids rebuilding pair keys and copying entire
    analytical DataFrames on every relationship request.
    """

    if df.empty:
        return df.copy()

    if "pair_key" not in df.columns:
        df = add_pair_column(df)

    if "pair_key" not in df.columns:
        return pd.DataFrame()

    return df.loc[
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

    try:
        pair_relationship = _query_relationship_state(
            pair_key
        )
    except FileNotFoundError as exc:
        raise ValueError(
            "Relationship-state layer is unavailable."
        ) from exc

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
    # Build temporal change episodes from detected change points
    # --------------------------------------------------------

    pair_change_points = filter_pair(
        pipeline["change_points"],
        pair_key
    )

    change_episodes = build_change_episodes(
        pair_change_points
    )
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
            pair_change_points,

        "change_episodes":
            change_episodes,

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