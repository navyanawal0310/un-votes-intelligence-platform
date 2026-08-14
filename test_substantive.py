from packages.warehouse.database import get_connection
from packages.analytics.substantive import substantive_disagreements


con = get_connection()

try:

    result = substantive_disagreements(
        con,
        "IND",
        "CHN",
    )

    print("\n")
    print("=" * 80)
    print("INDIA VS CHINA — SUBSTANTIVE DISAGREEMENTS")
    print("=" * 80)

    print("\nSUBSTANTIVE DISAGREEMENT COUNT")
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

    print("\nVOTE-PAIR DISTRIBUTION")
    print("-" * 80)

    distribution = (
        result
        .groupby(
            [
                "country_a_vote",
                "country_b_vote",
            ]
        )
        .size()
        .reset_index(name="count")
        .sort_values(
            "count",
            ascending=False,
        )
    )

    print(
        distribution.to_string(index=False)
    )

finally:
    con.close()