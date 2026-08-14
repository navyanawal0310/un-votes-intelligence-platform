from packages.warehouse.database import get_connection
from packages.analytics.analyzer import compare_countries


con = get_connection()

try:
    result = compare_countries(
        con,
        "IND",
        "CHN",
        min_common_events=20,
    )

    print("\n")
    print("=" * 70)
    print("COUNTRY COMPARISON")
    print("=" * 70)

    print("\nCOUNTRY A")
    print("-" * 70)
    print(
        result["profile_a"]
        .to_string(index=False)
    )

    print("\nCOUNTRY B")
    print("-" * 70)
    print(
        result["profile_b"]
        .to_string(index=False)
    )

    print("\nOVERALL SIMILARITY")
    print("-" * 70)
    print(
        result["similarity"]
        .to_string(index=False)
    )

    print("\nYEARLY SIMILARITY")
    print("-" * 70)
    print(
        result["yearly_similarity"]
        .to_string(index=False)
    )

    print("\nSUBSTANTIVE YEARLY SIMILARITY")
    print("-" * 70)
    print(
        result["substantive_yearly_similarity"]
        .to_string(index=False)
    )

finally:
    con.close()