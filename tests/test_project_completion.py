from pathlib import Path
import pandas as pd


# ============================================================
# UN VOTES ANALYZER
# PROJECT COMPLETION AUDIT
# ============================================================

ROOT = Path.cwd()


# ------------------------------------------------------------
# PROJECT COMPONENTS
# Weight reflects importance to the final system.
# Total = 100
# ------------------------------------------------------------

COMPONENTS = [
    {
        "name": "Core Data Pipeline",
        "weight": 12,
        "required": [
            "country_pair_alignment.csv",
            "country_pair_alignment_by_issue.csv",
            "country_pair_alignment_summary.csv",
        ],
    },
    {
        "name": "Pairwise Alignment Analytics",
        "weight": 10,
        "required": [
            "country_pair_alignment.csv",
            "country_pair_temporal_alignment.csv",
        ],
    },
    {
        "name": "Temporal Alignment Analysis",
        "weight": 10,
        "required": [
            "country_pair_temporal_alignment.csv",
        ],
    },
    {
        "name": "Change-Point Detection",
        "weight": 10,
        "required": [
            "temporal_alignment_change_points.csv",
            "temporal_alignment_change_episodes.csv",
        ],
    },
    {
        "name": "Historical Ground Truth",
        "weight": 8,
        "required": [
            "temporal_ground_truth.csv",
            "temporal_ground_truth_validation.csv",
        ],
    },
    {
        "name": "Temporal Event Validation",
        "weight": 10,
        "required": [
            "temporal_event_audit.csv",
            "temporal_event_conditioned_detection.csv",
        ],
    },
    {
        "name": "Quantitative Evaluation",
        "weight": 8,
        "required": [
            "temporal_quantitative_evaluation.csv",
            "temporal_quantitative_by_pair.csv",
        ],
    },
    {
        "name": "Error Analysis",
        "weight": 6,
        "required": [
            "temporal_error_analysis.csv",
        ],
    },
    {
        "name": "Robustness / Sensitivity",
        "weight": 6,
        "required": [
            "temporal_robustness_analysis.csv",
        ],
    },
    {
        "name": "Null / Chance Baseline",
        "weight": 5,
        "required": [
            "temporal_null_baseline.csv",
        ],
    },
    {
        "name": "Change-Point Explanation",
        "weight": 5,
        "required": [
            "change_point_explanations.csv",
        ],
    },
    {
        "name": "Final Intelligence Layer",
        "weight": 5,
        "required": [],
    },
    {
        "name": "User-Facing Dashboard",
        "weight": 3,
        "required": [],
    },
    {
        "name": "Documentation / Reproducibility",
        "weight": 2,
        "required": [],
    },
]


# ------------------------------------------------------------
# FILE CHECK
# ------------------------------------------------------------

def find_file(filename):
    """
    Search project root and common project directories.
    """
    locations = [
        ROOT / filename,
        ROOT / "data" / filename,
        ROOT / "data" / "validation" / filename,
        ROOT / "reports" / filename,
        ROOT / "outputs" / filename,
        ROOT / "results" / filename,
    ]

    for path in locations:
        if path.exists():
            return path

    return None


# ------------------------------------------------------------
# BASIC FILE QUALITY CHECK
# ------------------------------------------------------------

def inspect_csv(path):
    """
    Returns a lightweight quality assessment.
    """
    try:
        df = pd.read_csv(path)

        rows = len(df)
        columns = len(df.columns)

        if rows == 0:
            quality = "EMPTY"
        elif columns == 0:
            quality = "INVALID"
        else:
            quality = "VALID"

        return {
            "rows": rows,
            "columns": columns,
            "quality": quality,
        }

    except Exception as exc:
        return {
            "rows": 0,
            "columns": 0,
            "quality": f"ERROR: {exc}",
        }


# ------------------------------------------------------------
# COMPONENT STATUS
# ------------------------------------------------------------

def evaluate_component(component):
    required = component["required"]

    # Components that cannot yet be automatically verified
    if not required:
        return {
            "status": "NOT_VERIFIED",
            "completion": 0.0,
            "files_found": 0,
            "files_required": 0,
            "details": "Requires manual implementation review.",
        }

    found = []
    missing = []

    for filename in required:
        path = find_file(filename)

        if path:
            found.append((filename, path))
        else:
            missing.append(filename)

    ratio = len(found) / len(required)

    if ratio == 1:
        status = "COMPLETE"
    elif ratio > 0:
        status = "PARTIAL"
    else:
        status = "MISSING"

    details = []

    for filename, path in found:
        info = inspect_csv(path)

        details.append(
            f"{filename}: {info['quality']} "
            f"({info['rows']} rows, {info['columns']} columns)"
        )

    for filename in missing:
        details.append(f"{filename}: MISSING")

    return {
        "status": status,
        "completion": ratio,
        "files_found": len(found),
        "files_required": len(required),
        "details": " | ".join(details),
    }


# ------------------------------------------------------------
# VALIDATION COVERAGE
# ------------------------------------------------------------

def calculate_validation_coverage():
    """
    Estimates how much of the analytical validation framework
    has actually been executed based on generated outputs.
    """

    validation_outputs = [
        "temporal_ground_truth_validation.csv",
        "temporal_event_audit.csv",
        "temporal_event_conditioned_detection.csv",
        "temporal_quantitative_evaluation.csv",
        "temporal_quantitative_by_pair.csv",
        "temporal_error_analysis.csv",
        "temporal_robustness_analysis.csv",
        "temporal_null_baseline.csv",
    ]

    found = sum(find_file(x) is not None for x in validation_outputs)

    return found / len(validation_outputs)


# ------------------------------------------------------------
# ANALYTICAL COVERAGE
# ------------------------------------------------------------

def calculate_analytical_coverage():
    analytical_outputs = [
        "country_pair_alignment.csv",
        "country_pair_alignment_by_issue.csv",
        "country_pair_alignment_summary.csv",
        "country_pair_temporal_alignment.csv",
        "temporal_alignment_change_points.csv",
        "temporal_alignment_change_episodes.csv",
        "change_point_explanations.csv",
    ]

    found = sum(find_file(x) is not None for x in analytical_outputs)

    return found / len(analytical_outputs)


# ------------------------------------------------------------
# MAIN AUDIT
# ------------------------------------------------------------

def main():

    print()
    print("=" * 78)
    print("UN VOTES ANALYZER — PROJECT COMPLETION AUDIT")
    print("=" * 78)

    results = []

    weighted_completion = 0.0
    total_weight = 0

    for component in COMPONENTS:

        evaluation = evaluate_component(component)

        completion = evaluation["completion"]
        weight = component["weight"]

        weighted_completion += completion * weight
        total_weight += weight

        results.append({
            "component": component["name"],
            "weight": weight,
            "status": evaluation["status"],
            "completion": completion * 100,
            "files_found": evaluation["files_found"],
            "files_required": evaluation["files_required"],
        })

    overall_completion = weighted_completion / total_weight * 100

    validation_coverage = calculate_validation_coverage() * 100
    analytical_coverage = calculate_analytical_coverage() * 100

    df = pd.DataFrame(results)


    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 78)
    print("OVERALL PROJECT STATUS")
    print("=" * 78)

    print(f"Overall weighted completion:      {overall_completion:.1f}%")
    print(f"Analytical output coverage:       {analytical_coverage:.1f}%")
    print(f"Validation framework coverage:    {validation_coverage:.1f}%")


    # --------------------------------------------------------
    # COMPONENT TABLE
    # --------------------------------------------------------

    print()
    print("=" * 78)
    print("COMPONENT STATUS")
    print("=" * 78)

    print(
        df[
            [
                "component",
                "weight",
                "status",
                "completion",
                "files_found",
                "files_required",
            ]
        ].to_string(index=False)
    )


    # --------------------------------------------------------
    # CRITICAL GAPS
    # --------------------------------------------------------

    print()
    print("=" * 78)
    print("REMAINING / UNVERIFIED COMPONENTS")
    print("=" * 78)

    incomplete = df[df["completion"] < 100]

    if len(incomplete) == 0:
        print("No incomplete automatically-verifiable components found.")
    else:
        for _, row in incomplete.iterrows():
            print(
                f"- {row['component']}: "
                f"{row['completion']:.1f}% "
                f"[{row['status']}]"
            )


    # --------------------------------------------------------
    # SCIENTIFIC VALIDATION STATUS
    # --------------------------------------------------------

    print()
    print("=" * 78)
    print("SCIENTIFIC VALIDATION STATUS")
    print("=" * 78)

    print("Ground-truth events:             9")
    print("Measurable events:               3")
    print("Detected events:                 1")
    print("Observed detection rate:         0.111")
    print("Null mean detection rate:        0.059")
    print("Null 95th percentile:             0.222")
    print("Empirical p-value:                0.416")

    print()
    print(
        "Interpretation: The current temporal detection evidence "
        "does not establish statistically significant superiority "
        "over the random-timing baseline."
    )


    # --------------------------------------------------------
    # PROJECT MATURITY
    # --------------------------------------------------------

    print()
    print("=" * 78)
    print("PROJECT MATURITY")
    print("=" * 78)

    if overall_completion < 40:
        maturity = "FOUNDATION"
    elif overall_completion < 60:
        maturity = "ANALYTICAL PROTOTYPE"
    elif overall_completion < 75:
        maturity = "VALIDATED PROTOTYPE"
    elif overall_completion < 90:
        maturity = "ADVANCED PROTOTYPE"
    else:
        maturity = "NEAR PRODUCTION"

    print(f"Current maturity level: {maturity}")


    # --------------------------------------------------------
    # SAVE AUDIT
    # --------------------------------------------------------

    output = ROOT / "project_completion_audit.csv"

    df.to_csv(output, index=False)

    print()
    print("=" * 78)
    print("AUDIT COMPLETE")
    print("=" * 78)
    print(f"Saved audit: {output.name}")

    print()
    print(
        "IMPORTANT: The completion percentage measures implementation "
        "coverage, not scientific validity."
    )


if __name__ == "__main__":
    main()