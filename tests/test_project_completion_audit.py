"""
UN VOTES ANALYZER
PROJECT COMPLETION & EVIDENCE AUDIT

Purpose
-------
Estimate project completion using observable implementation,
testing, validation, robustness, intelligence, and reproducibility
evidence present in the repository.

IMPORTANT
---------
This is a project-audit tool, not a scientific validity claim.

A file existing does not automatically mean that a component is
scientifically validated. Validation evidence is assessed separately.

Status levels:
    0 = NOT STARTED
    1 = IMPLEMENTED
    2 = TESTED
    3 = VALIDATED

The final percentage is weighted across project components.
"""

from pathlib import Path
import pandas as pd


# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# WEIGHTS
# ============================================================

COMPONENTS = {
    "Data acquisition & preprocessing": 15,
    "Core alignment analysis": 15,
    "Temporal analysis": 15,
    "Historical ground truth": 10,
    "Quantitative validation": 15,
    "Robustness & sensitivity": 10,
    "Explanatory intelligence": 10,
    "Country-pair intelligence": 5,
    "Documentation & reproducibility": 5,
}


# ============================================================
# FILE GROUPS
# ============================================================

EVIDENCE = {

    "Data acquisition & preprocessing": {

        "implementation": [
            "data",
            "data/raw",
            "data/processed",
            "country_pair_alignment.csv",
            "country_pair_alignment_summary.csv",
        ],

        "testing": [
            "country_pair_alignment_summary.csv",
            "country_pair_alignment_by_issue.csv",
        ],

        "validation": [
            "country_pair_alignment_summary.csv",
        ],
    },

    "Core alignment analysis": {

        "implementation": [
            "country_pair_alignment.csv",
            "country_pair_alignment_by_issue.csv",
            "country_pair_alignment_summary.csv",
        ],

        "testing": [
            "country_pair_alignment_summary.csv",
        ],

        "validation": [
            "country_pair_alignment_summary.csv",
            "country_pair_alignment_by_issue.csv",
        ],
    },

    "Temporal analysis": {

        "implementation": [
            "country_pair_temporal_alignment.csv",
            "temporal_alignment_change_points.csv",
            "temporal_alignment_change_episodes.csv",
        ],

        "testing": [
            "test_temporal_episode_validation.py",
            "test_temporal_error_analysis.py",
            "test_temporal_event_signal.py",
        ],

        "validation": [
            "temporal_ground_truth_validation.csv",
            "temporal_event_signal_diagnostic.csv",
            "temporal_event_conditioned_detection.csv",
        ],
    },

    "Historical ground truth": {

        "implementation": [
            "data/validation/temporal_ground_truth.csv",
            "temporal_ground_truth.csv",
        ],

        "testing": [
            "test_temporal_ground_truth.py",
        ],

        "validation": [
            "temporal_ground_truth_validation.csv",
        ],
    },

    "Quantitative validation": {

        "implementation": [
            "test_temporal_quantitative_evaluation.py",
        ],

        "testing": [
            "test_temporal_quantitative_evaluation.py",
        ],

        "validation": [
            "temporal_quantitative_evaluation.csv",
            "temporal_quantitative_by_pair.csv",
        ],
    },

    "Robustness & sensitivity": {

        "implementation": [
            "test_temporal_robustness.py",
            "test_temporal_null_baseline.py",
        ],

        "testing": [
            "test_temporal_robustness.py",
            "test_temporal_null_baseline.py",
        ],

        "validation": [
            "temporal_robustness_analysis.csv",
            "temporal_null_baseline.csv",
        ],
    },

    "Explanatory intelligence": {

        "implementation": [
            "test_temporal_event_signal.py",
            "test_change_point_explanation.py",
            "test_temporal_issue_attribution.py",
            "test_temporal_issue_episode_attribution.py",
        ],

        "testing": [
            "test_change_point_explanation.py",
            "test_temporal_issue_attribution.py",
            "test_temporal_issue_episode_attribution.py",
        ],

        "validation": [
            "change_point_explanations.csv",
            "temporal_issue_attribution.csv",
            "temporal_issue_episode_attribution.csv",
        ],
    },

    "Country-pair intelligence": {

        "implementation": [
            "temporal_country_pair_scorecard.py",
        ],

        "testing": [
            "temporal_country_pair_scorecard.py",
        ],

        "validation": [
            "temporal_country_pair_scorecard.csv",
        ],
    },

    "Documentation & reproducibility": {

        "implementation": [
            "README.md",
            "requirements.txt",
            ".gitignore",
        ],

        "testing": [
            "README.md",
        ],

        "validation": [
            "README.md",
        ],
    },
}


# ============================================================
# HELPERS
# ============================================================

def exists(relative_path):
    """
    Check whether a file or directory exists.
    """
    return (BASE_DIR / relative_path).exists()


def count_existing(paths):
    """
    Count how many expected evidence items exist.
    """
    if not paths:
        return 0, 0

    existing = sum(
        1 for path in paths
        if exists(path)
    )

    return existing, len(paths)


def evidence_level(component):
    """
    Determine implementation/testing/validation level.

    Returns:
        0 = none
        1 = implementation
        2 = tested
        3 = validated
    """

    implementation = component.get(
        "implementation",
        []
    )

    testing = component.get(
        "testing",
        []
    )

    validation = component.get(
        "validation",
        []
    )

    implementation_count, implementation_total = (
        count_existing(implementation)
    )

    testing_count, testing_total = (
        count_existing(testing)
    )

    validation_count, validation_total = (
        count_existing(validation)
    )

    # --------------------------------------------------------
    # Require at least one implementation artifact
    # --------------------------------------------------------

    if implementation_count == 0:
        return 0

    # --------------------------------------------------------
    # Implementation exists
    # --------------------------------------------------------

    level = 1

    # --------------------------------------------------------
    # Tested
    #
    # A component is considered tested if either:
    #   - a dedicated test file exists, OR
    #   - its expected output artifact exists
    # --------------------------------------------------------

    if (
        testing_count > 0
        or validation_count > 0
    ):
        level = 2

    # --------------------------------------------------------
    # Validated
    #
    # Require validation evidence.
    # --------------------------------------------------------

    if validation_count > 0:
        level = 3

    return level


def status_name(level):
    return {
        0: "NOT STARTED",
        1: "IMPLEMENTED",
        2: "TESTED",
        3: "VALIDATED",
    }.get(level, "UNKNOWN")


def percentage_from_level(level):
    """
    Convert evidence level into completion credit.

    NOT STARTED = 0%
    IMPLEMENTED = 50%
    TESTED      = 75%
    VALIDATED   = 100%
    """

    return {
        0: 0.00,
        1: 0.50,
        2: 0.75,
        3: 1.00,
    }[level]


def existing_items(paths):
    return [
        path for path in paths
        if exists(path)
    ]


def missing_items(paths):
    return [
        path for path in paths
        if not exists(path)
    ]


# ============================================================
# AUDIT
# ============================================================

def run_audit():

    print()
    print("=" * 90)
    print("UN VOTES ANALYZER")
    print("PROJECT COMPLETION & EVIDENCE AUDIT")
    print("=" * 90)

    rows = []

    total_weight = 0
    weighted_completion = 0

    for component, weight in COMPONENTS.items():

        evidence = EVIDENCE.get(
            component,
            {}
        )

        implementation = evidence.get(
            "implementation",
            []
        )

        testing = evidence.get(
            "testing",
            []
        )

        validation = evidence.get(
            "validation",
            []
        )

        implementation_found = existing_items(
            implementation
        )

        testing_found = existing_items(
            testing
        )

        validation_found = existing_items(
            validation
        )

        level = evidence_level(evidence)

        completion_fraction = (
            percentage_from_level(level)
        )

        weighted_score = (
            weight * completion_fraction
        )

        total_weight += weight
        weighted_completion += weighted_score

        rows.append(
            {
                "component": component,
                "weight_percent": weight,
                "status": status_name(level),
                "completion_percent": (
                    completion_fraction * 100
                ),
                "weighted_contribution": weighted_score,
                "implementation_evidence": len(
                    implementation_found
                ),
                "testing_evidence": len(
                    testing_found
                ),
                "validation_evidence": len(
                    validation_found
                ),
                "implementation_total": len(
                    implementation
                ),
                "testing_total": len(
                    testing
                ),
                "validation_total": len(
                    validation
                ),
            }
        )

    result = pd.DataFrame(rows)

    overall_completion = (
        weighted_completion /
        total_weight *
        100
    )

    return result, overall_completion


# ============================================================
# PRINT DETAILED REPORT
# ============================================================

def print_report(result, overall_completion):

    print()
    print("=" * 90)
    print("COMPONENT STATUS")
    print("=" * 90)

    display_columns = [
        "component",
        "weight_percent",
        "status",
        "completion_percent",
        "weighted_contribution",
    ]

    print(
        result[
            display_columns
        ].to_string(index=False)
    )

    print()
    print("=" * 90)
    print("OVERALL PROJECT COMPLETION")
    print("=" * 90)

    print(
        f"Weighted completion: "
        f"{overall_completion:.1f}%"
    )

    print()
    print("STATUS DISTRIBUTION")

    status_counts = (
        result["status"]
        .value_counts()
    )

    for status in [
        "VALIDATED",
        "TESTED",
        "IMPLEMENTED",
        "NOT STARTED",
    ]:
        print(
            f"{status:<15}: "
            f"{int(status_counts.get(status, 0))}"
        )

    # --------------------------------------------------------
    # Major layer summaries
    # --------------------------------------------------------

    print()
    print("=" * 90)
    print("MAJOR PROJECT LAYERS")
    print("=" * 90)

    layers = {

        "Core analytical engine": [
            "Data acquisition & preprocessing",
            "Core alignment analysis",
            "Temporal analysis",
        ],

        "Validation framework": [
            "Historical ground truth",
            "Quantitative validation",
            "Robustness & sensitivity",
        ],

        "Intelligence layer": [
            "Explanatory intelligence",
            "Country-pair intelligence",
        ],

        "Reproducibility": [
            "Documentation & reproducibility",
        ],
    }

    for layer_name, components in layers.items():

        layer = result[
            result["component"].isin(components)
        ]

        layer_weight = layer[
            "weight_percent"
        ].sum()

        layer_score = layer[
            "weighted_contribution"
        ].sum()

        if layer_weight > 0:
            layer_percent = (
                layer_score /
                layer_weight *
                100
            )
        else:
            layer_percent = 0

        if layer_percent >= 90:
            layer_status = "COMPLETE"

        elif layer_percent >= 70:
            layer_status = "SUBSTANTIALLY COMPLETE"

        elif layer_percent >= 40:
            layer_status = "PARTIAL"

        else:
            layer_status = "EARLY STAGE"

        print(
            f"{layer_name:<30} "
            f"{layer_percent:6.1f}%  "
            f"{layer_status}"
        )

    # --------------------------------------------------------
    # Validation warning
    # --------------------------------------------------------

    validation_components = result[
        result["component"].isin(
            [
                "Historical ground truth",
                "Quantitative validation",
                "Robustness & sensitivity",
            ]
        )
    ]

    validation_weight = validation_components[
        "weight_percent"
    ].sum()

    validation_score = validation_components[
        "weighted_contribution"
    ].sum()

    validation_percent = (
        validation_score /
        validation_weight *
        100
    )

    print()
    print("=" * 90)
    print("VALIDATION INTERPRETATION")
    print("=" * 90)

    if validation_percent >= 90:

        print(
            "The validation framework is substantially "
            "complete."
        )

    elif validation_percent >= 70:

        print(
            "The validation framework is strong but "
            "still has measurable gaps."
        )

    else:

        print(
            "The validation framework remains incomplete."
        )

    print(
        "The completion percentage measures project "
        "development maturity, not scientific truth."
    )

    print(
        "A validated component means that the repository "
        "contains explicit validation evidence."
    )


# ============================================================
# MISSING EVIDENCE REPORT
# ============================================================

def print_missing_evidence():

    print()
    print("=" * 90)
    print("MISSING EVIDENCE")
    print("=" * 90)

    anything_missing = False

    for component, evidence in EVIDENCE.items():

        missing = []

        for evidence_type in [
            "implementation",
            "testing",
            "validation",
        ]:

            paths = evidence.get(
                evidence_type,
                []
            )

            for path in missing_items(paths):

                missing.append(
                    f"{evidence_type}: {path}"
                )

        if missing:

            anything_missing = True

            print()
            print(component)

            for item in missing:
                print(
                    f"  - {item}"
                )

    if not anything_missing:
        print(
            "No expected evidence items are missing."
        )


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(result, overall_completion):

    output_file = (
        BASE_DIR /
        "project_completion_audit.csv"
    )

    result = result.copy()

    result["overall_project_completion_percent"] = (
        overall_completion
    )

    result.to_csv(
        output_file,
        index=False,
        float_format="%.4f"
    )

    print()
    print(
        f"Saved audit: {output_file}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    result, overall_completion = run_audit()

    print_report(
        result,
        overall_completion
    )

    print_missing_evidence()

    save_results(
        result,
        overall_completion
    )

    print()
    print("=" * 90)
    print("PROJECT COMPLETION AUDIT COMPLETE")
    print("=" * 90)


if __name__ == "__main__":
    main()