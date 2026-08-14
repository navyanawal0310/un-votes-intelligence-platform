"""
Test runner for UN voting analytics.
"""

from packages.warehouse.database import get_connection
from packages.analytics.queries import (
    country_voting_profile,
    country_voting_similarity,
    rank_country_similarity,
    country_similarity_by_year,
    country_substantive_similarity_by_year,
)


con = get_connection()

try:
    df = country_voting_profile(con)

    print("\nCOUNTRY VOTING PROFILE")
    print("-" * 80)

    print(df.head(20).to_string(index=False))

    print("\nRows returned:", len(df))
    print("\nCOUNTRY VOTING SIMILARITY")
    print("-" * 80)

    similarity = country_voting_similarity(
        con,
        "IND",
        "CHN",
    )

    print(similarity.to_string(index=False))

    print("\nCOUNTRIES MOST SIMILAR TO INDIA")
    print("-" * 80)
    ranking = rank_country_similarity(
        con,
        "IND",
    )
    print(
        ranking.head(20).to_string(index=False)
    )
    print("\nCountries ranked:", len(ranking))

    print("\nINDIA vs CHINA — YEARLY VOTING SIMILARITY")
    print("-" * 80)
    yearly_similarity = country_similarity_by_year(
        con,
        "IND",
        "CHN",
    )
    print(
        yearly_similarity.to_string(index=False)
    )
    print(
        "\nYears returned:",
        len(yearly_similarity)
    )

    print("\nINDIA vs CHINA — SUBSTANTIVE YEARLY SIMILARITY")
    print("-" * 80)
    substantive = country_substantive_similarity_by_year(
        con,
        "IND",
        "CHN",
        min_common_events=20,
    )
    print(
        substantive.to_string(index=False)
    )
    print(
        "\nYears returned:",
        len(substantive)
    )

finally:
    con.close()

