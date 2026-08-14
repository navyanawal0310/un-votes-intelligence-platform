from packages.warehouse.database import get_connection
from packages.analytics.disagreements import disagreement_summary


con = get_connection()

try:

    result = disagreement_summary(
        con,
        "IND",
        "CHN",
    )

    print("\n")
    print("=" * 70)
    print("INDIA VS CHINA — DISAGREEMENT TYPES")
    print("=" * 70)

    print(
        result.to_string(index=False)
    )

    print(
        f"\nTotal disagreement events: "
        f"{result['disagreement_count'].sum():,}"
    )

finally:
    con.close()