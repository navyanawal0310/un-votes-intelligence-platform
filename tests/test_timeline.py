from packages.warehouse.database import get_connection

from packages.analytics.timeline import (
    country_agreement_timeline,
    country_vote_timeline,
    bloc_agreement_timeline,
)


con = get_connection()

try:

    # ---------------------------------------------------------
    # INDIA VS CHINA
    # ---------------------------------------------------------

    print("=" * 80)
    print("INDIA VS CHINA — AGREEMENT TIMELINE")
    print("=" * 80)

    india_china = country_agreement_timeline(
        con,
        "IND",
        "CHN",
    )

    print(india_china.to_string(index=False))
    print(f"\nYears returned: {len(india_china):,}")

    # ---------------------------------------------------------
    # INDIA VOTING BEHAVIOR
    # ---------------------------------------------------------

    print("\n")
    print("=" * 80)
    print("INDIA — VOTING TIMELINE")
    print("=" * 80)

    india = country_vote_timeline(
        con,
        "IND",
    )

    print(india.to_string(index=False))
    print(f"\nYears returned: {len(india):,}")

    # ---------------------------------------------------------
    # INDIA VS ASIA-PACIFIC BLOC
    # ---------------------------------------------------------

    asia_pacific = [
        "CHN",
        "JPN",
        "IDN",
        "MYS",
        "SGP",
        "THA",
        "VNM",
        "PHL",
        "BGD",
        "LKA",
        "NPL",
    ]

    print("\n")
    print("=" * 80)
    print("INDIA VS ASIA-PACIFIC — AGREEMENT TIMELINE")
    print("=" * 80)

    bloc = bloc_agreement_timeline(
        con,
        "IND",
        asia_pacific,
    )

    print(bloc.to_string(index=False))
    print(f"\nYears returned: {len(bloc):,}")

finally:
    con.close()