"""
UN VOTES ANALYZER
CANONICAL PIPELINE

Integration/orchestration layer.

This pipeline does NOT invent analytical modules.
It validates the analytical artifacts already produced by
the research pipeline and then connects them into the
canonical analytical data layer.

Architecture:

    Analytical Outputs
            ↓
    Artifact Validation
            ↓
    Canonical Analytical Pipeline
            ↓
    Country-Pair Scorecard
            ↓
    Intelligence Interface
"""

from pathlib import Path
import sys
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# ANALYTICAL ARTIFACTS
# ============================================================

ARTIFACTS = {

    # --------------------------------------------------------
    # Core temporal analysis
    # --------------------------------------------------------

    "country_pair_alignment":
        "country_pair_alignment_summary.csv",

    "country_pair_temporal_alignment":
        "country_pair_temporal_alignment.csv",

    "change_points":
        "temporal_alignment_change_points.csv",

    # --------------------------------------------------------
    # Ground truth / validation
    # --------------------------------------------------------

    "ground_truth":
        "data/validation/temporal_ground_truth.csv",

    "ground_truth_validation":
        "temporal_ground_truth_validation.csv",

    "quantitative_evaluation":
        "temporal_quantitative_evaluation.csv",

    "error_analysis":
        "temporal_error_analysis.csv",

    "quantitative_by_pair":
        "temporal_quantitative_by_pair.csv",

    # --------------------------------------------------------
    # Event analysis
    # --------------------------------------------------------

    "event_conditioned":
        "temporal_event_conditioned_detection.csv",

    "event_signal":
        "temporal_event_signal_diagnostic.csv",

    "detection_coverage":
        "temporal_detection_coverage.csv",

    # --------------------------------------------------------
    # Robustness / null model
    # --------------------------------------------------------

    "robustness":
        "temporal_robustness_analysis.csv",

    "null_baseline":
        "temporal_null_baseline.csv",

    # --------------------------------------------------------
    # Attribution
    # --------------------------------------------------------

    "issue_attribution":
        "change_point_explanations.csv",

    "episode_attribution":
        "temporal_issue_episode_attribution.csv",

    "attribution_robustness":
        "temporal_issue_attribution_robustness.csv",

    "attribution_robustness_summary":
        "temporal_issue_attribution_robustness_summary.csv",

    # --------------------------------------------------------
    # Intelligence
    # --------------------------------------------------------

    "scorecard":
        "temporal_country_pair_scorecard.csv",

    "intelligence":
        "temporal_country_pair_intelligence.csv",
}


# ============================================================
# LOAD ARTIFACT
# ============================================================

def load_artifact(path):

    try:

        df = pd.read_csv(path)

        return df

    except Exception as error:

        print(
            f"[FAIL] Could not read {path.name}: {error}"
        )

        return None


# ============================================================
# VALIDATE ARTIFACTS
# ============================================================

def validate_artifacts():

    print()
    print("=" * 80)
    print("ANALYTICAL ARTIFACT VALIDATION")
    print("=" * 80)

    results = {}

    for name, filename in ARTIFACTS.items():

        path = BASE_DIR / filename

        if not path.exists():

            print(
                f"[MISSING] {name:<35} {filename}"
            )

            results[name] = False

            continue

        df = load_artifact(path)

        if df is None:

            results[name] = False

            continue

        if df.empty:

            print(
                f"[EMPTY]   {name:<35} {filename}"
            )

            results[name] = False

            continue

        print(
            f"[OK]      {name:<35} "
            f"{len(df)} rows"
        )

        results[name] = True

    return results


# ============================================================
# VALIDATE COUNTRY PAIRS
# ============================================================

def validate_country_pairs():

    path = (
        BASE_DIR /
        ARTIFACTS["scorecard"]
    )

    if not path.exists():

        print(
            "[FAIL] Scorecard does not exist."
        )

        return False

    df = pd.read_csv(path)

    if "pair" not in df.columns:

        print(
            "[FAIL] Scorecard does not contain "
            "'pair' column."
        )

        return False

    pairs = (
        df["pair"]
        .dropna()
        .astype(str)
        .str.upper()
        .unique()
    )

    print()
    print("=" * 80)
    print("COUNTRY-PAIR INTEGRATION")
    print("=" * 80)

    print()
    print(
        f"Country pairs available: {len(pairs)}"
    )

    for pair in sorted(pairs):

        print(
            f"  {pair}"
        )

    return len(pairs) > 0


# ============================================================
# CANONICAL PIPELINE CHECK
# ============================================================

def validate_canonical_pipeline():

    print()
    print("=" * 80)
    print("CANONICAL PIPELINE")
    print("=" * 80)

    try:

        from analytical_pipeline import (
            load_pipeline,
            available_pairs,
        )

        pipeline = load_pipeline()

        pairs = available_pairs(
            pipeline
        )

        print()
        print(
            f"[OK] Canonical analytical pipeline loaded"
        )

        print(
            f"[OK] Available country pairs: {len(pairs)}"
        )

        for pair in pairs:

            print(
                f"     {pair}"
            )

        return True

    except Exception as error:

        print()
        print(
            "[FAIL] Canonical analytical pipeline"
        )

        print(
            f"{type(error).__name__}: {error}"
        )

        return False


# ============================================================
# PIPELINE SUMMARY
# ============================================================

def print_summary(
    artifact_results,
    pair_ok,
    canonical_ok,
):

    print()
    print("=" * 80)
    print("PIPELINE SUMMARY")
    print("=" * 80)

    total = len(artifact_results)

    passed = sum(
        artifact_results.values()
    )

    missing = total - passed

    print()
    print(
        f"Artifacts checked: {total}"
    )

    print(
        f"Artifacts available: {passed}"
    )

    print(
        f"Artifacts missing/invalid: {missing}"
    )

    print(
        f"Country-pair integration: "
        f"{'PASS' if pair_ok else 'FAIL'}"
    )

    print(
        f"Canonical pipeline: "
        f"{'PASS' if canonical_ok else 'FAIL'}"
    )

    print()

    if missing == 0 and pair_ok and canonical_ok:

        print(
            "PIPELINE STATUS: READY"
        )

    else:

        print(
            "PIPELINE STATUS: INCOMPLETE"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("UN VOTES ANALYZER — CANONICAL PIPELINE")
    print("=" * 80)

    print()
    print(
        f"Repository: {BASE_DIR}"
    )

    artifact_results = (
        validate_artifacts()
    )

    pair_ok = (
        validate_country_pairs()
    )

    canonical_ok = (
        validate_canonical_pipeline()
    )

    print_summary(
        artifact_results,
        pair_ok,
        canonical_ok,
    )

    if (
        not pair_ok
        or not canonical_ok
    ):

        sys.exit(1)


if __name__ == "__main__":
    main()