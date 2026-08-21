"""
UN VOTES ANALYZER
VALIDATION COMPLETENESS AUDIT

Purpose
-------
Determine whether the project contains the required validation
evidence.

IMPORTANT:
This measures VALIDATION COVERAGE, not model accuracy.

A component is considered present when the required evidence
exists in the repository.
"""

from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# VALIDATION EVIDENCE
# ============================================================

VALIDATION_COMPONENTS = {

    "Ground-truth dataset": [
        "data/validation/temporal_ground_truth.csv",
        "temporal_ground_truth.csv",
    ],

    "Ground-truth validation": [
        "temporal_ground_truth_validation.csv",
    ],

    "Exact and tolerance detection evaluation": [
        "temporal_quantitative_evaluation.csv",
    ],

    "Temporal error analysis": [
        "temporal_error_analysis.csv",
    ],

    "Country-pair validation": [
        "temporal_quantitative_by_pair.csv",
    ],

    "Event-conditioned detection": [
        "temporal_event_conditioned_detection.csv",
    ],

    "Temporal event signal diagnostics": [
        "temporal_event_signal_diagnostic.csv",
    ],

    "Robustness / sensitivity analysis": [
        "temporal_robustness_analysis.csv",
    ],

    "Null / random baseline": [
        "temporal_null_baseline.csv",
    ],

    "Issue attribution": [
        "change_point_explanations.csv",
    ],

    "Validation test scripts": [
    "__AUTO_DISCOVER_TEMPORAL_TESTS__",
],
}


# ============================================================
# FIND EXISTING FILES
# ============================================================

def existing_files(file_list):

    found = []

    for relative_path in file_list:

        # ----------------------------------------------------
        # Automatically discover temporal validation scripts
        # ----------------------------------------------------

        if relative_path == "__AUTO_DISCOVER_TEMPORAL_TESTS__":

            for path in sorted(
                BASE_DIR.glob("test_temporal_*.py")
            ):

                found.append(
                    path.relative_to(BASE_DIR).as_posix()
                )

            continue

        # ----------------------------------------------------
        # Normal file
        # ----------------------------------------------------

        path = BASE_DIR / relative_path

        if path.exists():

            found.append(
                path.relative_to(BASE_DIR).as_posix()
            )

    return found

# ============================================================
# AUDIT
# ============================================================

# ============================================================
# AUDIT
# ============================================================

def run_audit():

    rows = []

    for component, required_files in VALIDATION_COMPONENTS.items():

        found = existing_files(required_files)

        total_required = len(required_files)
        total_found = len(found)

        # ----------------------------------------------------
        # Validation test scripts
        # ----------------------------------------------------
        # These are discovered dynamically using:
        # test_temporal_*.py
        # ----------------------------------------------------

        if component == "Validation test scripts":

            if total_found > 0:
                status = "PRESENT"
            else:
                status = "MISSING"

        # ----------------------------------------------------
        # Normal validation evidence
        # ----------------------------------------------------
        # For these components, the listed files are
        # acceptable evidence locations / alternatives.
        #
        # Therefore:
        #   >= 1 found  -> PRESENT
        #   0 found     -> MISSING
        # ----------------------------------------------------

        else:

            if total_found > 0:
                status = "PRESENT"
            else:
                status = "MISSING"

        rows.append(
            {
                "validation_component": component,
                "status": status,
                "required_files": total_required,
                "found_files": total_found,
                "evidence": "; ".join(found),
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# CALCULATE COVERAGE
# ============================================================

def calculate_coverage(result):

    scores = []

    for _, row in result.iterrows():

        if row["status"] == "PRESENT":

            scores.append(1.0)

        elif row["status"] == "PARTIAL":

            scores.append(
                row["found_files"] /
                row["required_files"]
            )

        else:

            scores.append(0.0)

    return sum(scores) / len(scores) * 100


# ============================================================
# PRINT REPORT
# ============================================================

def print_report(result, coverage):

    print()
    print("=" * 90)
    print("VALIDATION COMPLETENESS AUDIT")
    print("=" * 90)

    print()

    for _, row in result.iterrows():

        print(
            f"{row['validation_component']:<42} "
            f"{row['status']:<10} "
            f"{row['found_files']}/{row['required_files']}"
        )

    print()
    print("=" * 90)
    print("VALIDATION COVERAGE")
    print("=" * 90)

    total = len(result)

    present = (
        result["status"] == "PRESENT"
    ).sum()

    partial = (
        result["status"] == "PARTIAL"
    ).sum()

    missing = (
        result["status"] == "MISSING"
    ).sum()

    print(
        f"Validation components: {total}"
    )

    print(
        f"Fully present:         {present}"
    )

    print(
        f"Partially present:     {partial}"
    )

    print(
        f"Missing:               {missing}"
    )

    print(
        f"Validation coverage:   {coverage:.1f}%"
    )

    print()

    if coverage >= 95:

        assessment = (
            "VALIDATION FRAMEWORK SUBSTANTIALLY COMPLETE"
        )

    elif coverage >= 75:

        assessment = (
            "VALIDATION FRAMEWORK STRONG"
        )

    elif coverage >= 50:

        assessment = (
            "VALIDATION FRAMEWORK PARTIALLY COMPLETE"
        )

    else:

        assessment = (
            "VALIDATION FRAMEWORK INCOMPLETE"
        )

    print(
        f"Assessment: {assessment}"
    )

    print()

    print("IMPORTANT:")

    print(
        "Validation coverage measures whether the required "
        "evaluation evidence exists."
    )

    print(
        "It does NOT measure scientific accuracy or model quality."
    )

    print(
        "Performance must be evaluated using the quantitative "
        "validation results."
    )


# ============================================================
# INCOMPLETE COMPONENTS
# ============================================================

def print_incomplete(result):

    incomplete = result[
        result["status"] != "PRESENT"
    ]

    print()
    print("=" * 90)
    print("INCOMPLETE VALIDATION COMPONENTS")
    print("=" * 90)

    if incomplete.empty:

        print()
        print(
            "ALL REQUIRED VALIDATION COMPONENTS ARE PRESENT."
        )

        return

    for _, row in incomplete.iterrows():

        print()

        print(
            f"[{row['status']}] "
            f"{row['validation_component']}"
        )

        print(
            f"Required files: {row['required_files']}"
        )

        print(
            f"Found files:    {row['found_files']}"
        )

        if row["evidence"]:

            print(
                f"Evidence:       {row['evidence']}"
            )


# ============================================================
# SAVE
# ============================================================

def save_result(result, coverage):

    output = (
        BASE_DIR /
        "validation_completeness_audit.csv"
    )

    result = result.copy()

    result[
        "validation_coverage_percent"
    ] = coverage

    result.to_csv(
        output,
        index=False
    )

    print()
    print(
        f"Saved validation audit: {output}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    result = run_audit()

    coverage = calculate_coverage(
        result
    )

    print_report(
        result,
        coverage
    )

    print_incomplete(
        result
    )

    save_result(
        result,
        coverage
    )

    print()
    print("=" * 90)
    print(
        "VALIDATION COMPLETENESS AUDIT COMPLETE"
    )
    print("=" * 90)


if __name__ == "__main__":
    main()