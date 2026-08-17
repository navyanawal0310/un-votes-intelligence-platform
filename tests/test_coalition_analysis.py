"""
Test runner for coalition intelligence analytics.
"""

from packages.warehouse.database import get_connection

from packages.analytics.coalition_analysis import (
    strongest_coalitions,
    coalition_profile,
    coalition_trend,
    coalition_trend_change,
)


def print_section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


con = get_connection()

try:

    # ---------------------------------------------------------
    # 1. Strongest country-pair coalitions
    # ---------------------------------------------------------

    print_section("STRONGEST VOTING COALITIONS")

    strongest = strongest_coalitions(
        con,
        min_common_votes=100,
        min_agreement=75.0,
        limit=20,
    )

    if strongest.empty:
        print("No coalition relationships found.")
    else:
        print(strongest.to_string(index=False))

    print(
        f"\nCoalition relationships returned: "
        f"{len(strongest):,}"
    )

    # ---------------------------------------------------------
    # 2. India coalition profile
    # ---------------------------------------------------------

    print_section("INDIA — COALITION PROFILE")

    india = coalition_profile(
        con,
        "IND",
        min_common_votes=100,
        limit=20,
    )

    if india.empty:
        print("No coalition partners found.")
    else:
        print(india.to_string(index=False))

    print(
        f"\nIndia coalition partners returned: "
        f"{len(india):,}"
    )

    # ---------------------------------------------------------
    # 3. India-China yearly coalition trend
    # ---------------------------------------------------------

    print_section("INDIA VS CHINA — COALITION TREND")

    trend = coalition_trend(
        con,
        "IND",
        "CHN",
        min_common_votes=5,
    )

    if trend.empty:
        print("No yearly coalition observations found.")
    else:
        print(trend.to_string(index=False))

    print(
        f"\nYears returned: {len(trend):,}"
    )

    # ---------------------------------------------------------
    # 4. India-China coalition direction
    # ---------------------------------------------------------

    print_section(
        "INDIA VS CHINA — COALITION DIRECTION"
    )

    change = coalition_trend_change(
        con,
        "IND",
        "CHN",
        min_common_votes=5,
    )

    if change.empty:
        print("Unable to determine coalition direction.")
    else:
        print(change.to_string(index=False))

    # ---------------------------------------------------------
    # Final status
    # ---------------------------------------------------------

    print_section(
        "COALITION ANALYTICS TEST COMPLETE"
    )

    print(
        "Coalition analytics test runner: PASSED"
    )

finally:
    con.close()