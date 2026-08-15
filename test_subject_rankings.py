"""
Test runner for subject-level voting rankings.
"""

from packages.warehouse.database import get_connection
from packages.analytics.subject_rankings import subject_rankings


def main() -> None:

    con = get_connection()

    try:
        country_a = "IND"
        country_b = "CHN"

        print("=" * 80)
        print("INDIA VS CHINA — SUBJECT DISAGREEMENT RANKINGS")
        print("=" * 80)

        result = subject_rankings(
            con,
            "IND",
            "CHN",
            min_events=10,
            order_by="disagreement",
        )

        if result.empty:
            print("\nNo subject-level voting data found.")
            return

        print(
            result.to_string(index=False)
        )

        print(
            f"\nSubjects ranked: {len(result):,}"
        )

    finally:
        con.close()


if __name__ == "__main__":
    main()