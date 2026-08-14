from packages.warehouse.database import get_connection
from packages.analytics.resolutions import country_disagreements


con = get_connection()

try:

    result = country_disagreements(
        con,
        "IND",
        "CHN",
    )

    print("\n")
    print("=" * 80)
    print("INDIA VS CHINA — DISAGREEMENT RESOLUTIONS")
    print("=" * 80)

    print("\nDISAGREEMENT COUNT")
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

finally:
    con.close()