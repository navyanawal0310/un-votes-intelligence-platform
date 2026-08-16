from packages.warehouse.database import get_connection

from packages.analytics.issue_positions import (
    issue_positions,
    issue_position_summary,
)


con = get_connection()

try:

    print("=" * 80)
    print("INDIA — ISSUE POSITIONS")
    print("=" * 80)

    result = issue_positions(
        con,
        "IND",
        min_events=5,
    )

    print(result.head(30).to_string(index=False))

    print(f"\nRows returned: {len(result):,}")

    print("\n")
    print("=" * 80)
    print("INDIA — ISSUE POSITION SUMMARY")
    print("=" * 80)

    summary = issue_position_summary(
        con,
        "IND",
        min_events=10,
    )

    print(summary.head(30).to_string(index=False))

    print(f"\nIssues returned: {len(summary):,}")

finally:
    con.close()