from packages.warehouse.database import get_connection

from packages.analytics.change_points import (
    detect_change_points,
    rank_change_points,
)


con = get_connection()

try:

    print("=" * 80)
    print("INDIA — NUCLEAR DISARMAMENT CHANGE POINTS")
    print("=" * 80)

    issue = "NUCLEAR DISARMAMENT"

    result = detect_change_points(
        con,
        "IND",
        issue,
        min_events=1,
        min_shift=0.20,
    )

    print(result.to_string(index=False))

    print(f"\nChange points detected: {len(result):,}")

    print("\n")
    print("=" * 80)
    print("INDIA — LARGEST ISSUE POSITION SHIFTS")
    print("=" * 80)

    ranked = rank_change_points(
        con,
        "IND",
        min_events=3,
        min_shift=0.20,
    )

    print(
        ranked.head(30).to_string(index=False)
    )

    print(
        f"\nChange points ranked: {len(ranked):,}"
    )

finally:
    con.close()