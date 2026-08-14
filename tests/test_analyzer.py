import pandas as pd

from packages.warehouse.database import get_connection
from packages.analytics.analyzer import analyze_country


con = get_connection()

try:

    result = analyze_country(
        con,
        "IND",
        top_n=20,
    )

    print("\n")
    print("=" * 70)
    print("UN VOTES ANALYZER — INDIA")
    print("=" * 70)

    print("\nCOUNTRY PROFILE")
    print("-" * 70)
    print(result["profile"].to_string(index=False))

    print("\nMOST SIMILAR COUNTRIES")
    print("-" * 70)
    print(
        result["similar_countries"]
        .to_string(index=False)
    )

    print("\nINDIA VS CHINA — YEARLY")
    print("-" * 70)
    print(
        result["yearly_similarity"]
        .to_string(index=False)
    )

    print("\nINDIA VS CHINA — SUBSTANTIVE YEARLY")
    print("-" * 70)
    print(
        result["substantive_yearly_similarity"]
        .to_string(index=False)
    )

finally:
    con.close()