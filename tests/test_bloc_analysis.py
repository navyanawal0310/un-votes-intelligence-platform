from packages.warehouse.database import get_connection
from packages.analytics.bloc_analysis import (
    country_vs_bloc,
    bloc_voting_profile,
)


con = get_connection()

try:

    print("=" * 80)
    print("INDIA VS ASIA-PACIFIC BLOC")
    print("=" * 80)

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

    result = country_vs_bloc(
        con,
        "IND",
        asia_pacific,
    )

    print(result.to_string(index=False))

    print("\n")
    print("=" * 80)
    print("INDIA VS ASIA-PACIFIC — VOTE PROFILE")
    print("=" * 80)

    profile = bloc_voting_profile(
        con,
        "IND",
        asia_pacific,
    )

    print(profile.to_string(index=False))

finally:
    con.close()