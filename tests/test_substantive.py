from packages.warehouse.database import get_connection
from packages.analytics.substantive import (substantive_disagreements, top_disputed_resolutions,
    substantive_disagreement_by_year,substantive_disagreement_by_subject,top_substantive_disagreement_subjects,)


con = get_connection()

try:

    result = substantive_disagreements(
        con,
        "IND",
        "CHN",
    )

    print("\n")
    print("=" * 80)
    print("INDIA VS CHINA — SUBSTANTIVE DISAGREEMENTS")
    print("=" * 80)

    print("\nSUBSTANTIVE DISAGREEMENT COUNT")
    print("-" * 80)
    print(f"Rows returned: {len(result):,}")

    print("\nSAMPLE")
    print("-" * 80)

    print(
        result[
            [
                "resolution_code",
                "resolution_title",
                "full_date",
                "country_a_vote",
                "country_b_vote",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

    print("\nVOTE-PAIR DISTRIBUTION")
    print("-" * 80)

    distribution = (
        result
        .groupby(
            [
                "country_a_vote",
                "country_b_vote",
            ]
        )
        .size()
        .reset_index(name="count")
        .sort_values(
            "count",
            ascending=False,
        )
    )

    print(
        distribution.to_string(index=False)
    )
    print("\n")
    print("=" * 80)
    print("INDIA VS CHINA — TOP DISPUTED RESOLUTIONS")
    print("=" * 80)

    top = top_disputed_resolutions(
        con,
        "IND",
        "CHN",
        limit=20,
    )

    print("\nTOP 20")
    print("-" * 80)

    print(
        top[
            [
                "resolution_code",
                "full_date",
                "disagreement_count",
                "resolution_title",
            ]
        ].to_string(index=False)
    )
    print("\n")
    print("=" * 80)
    print("INDIA VS CHINA — SUBSTANTIVE DISAGREEMENT BY YEAR")
    print("=" * 80)

    yearly = substantive_disagreement_by_year(
        con,
        "IND",
        "CHN",
    )
    print(
        yearly[
            [
                "year",
                "substantive_voting_events",
                "matching_votes",
                "different_votes",
                "agreement_percentage",
                "disagreement_percentage",
            ]
        ].to_string(index=False)
    )
    print(f"\nYears returned: {len(yearly):,}")
    print("\n")
    print("=" * 80)
    print("INDIA VS CHINA — SUBSTANTIVE DISAGREEMENT BY SUBJECT")
    print("=" * 80)

    subject_result = substantive_disagreement_by_subject(
        con,
        "IND",
        "CHN",
    )

    print(
        subject_result[
            [
                "subject",
                "substantive_voting_events",
                "matching_votes",
                "different_votes",
                "agreement_percentage",
                "disagreement_percentage",
            ]
        ].head(30).to_string(index=False)
    )

    print(f"\nSubjects returned: {len(subject_result):,}")
    print("\n")
    print("=" * 80)
    print("INDIA VS CHINA — TOP SUBSTANTIVE DISAGREEMENT SUBJECTS")
    print("=" * 80)

    top_subjects = top_substantive_disagreement_subjects(
        con,
        "IND",
        "CHN",
        limit=20,
        min_events=10,
    )

    print(
        top_subjects[
            [
                "subject",
                "substantive_voting_events",
                "matching_votes",
                "different_votes",
                "agreement_percentage",
                "disagreement_percentage",
            ]
        ].to_string(index=False)
)

finally:
    con.close()