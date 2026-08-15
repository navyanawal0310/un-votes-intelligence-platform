"""
Test runner for subject-level voting trends.
"""

from packages.warehouse.database import get_connection
from packages.analytics.subject_trends import subject_voting_trend


def main() -> None:

    con = get_connection()

    country_a = "IND"
    country_b = "CHN"
    subject = "NUCLEAR DISARMAMENT"

    try:
        print("=" * 80)
        print("INDIA VS CHINA — SUBJECT VOTING TREND")
        print("=" * 80)

        print(f"\nSubject: {subject}")
        print(f"Country A: {country_a}")
        print(f"Country B: {country_b}")

        trend = subject_voting_trend(
            con,
            country_a,
            country_b,
            subject,
        )

        print("\nRESULT")
        print("-" * 80)

        if trend.empty:
            print("No voting data found for this subject.")
            print("\nCheck the exact subject name in dim_resolution.")
            return

        print(
            trend.to_string(index=False)
        )

        print(
            f"\nYears returned: {len(trend):,}"
        )

    finally:
        con.close()


if __name__ == "__main__":
    main()