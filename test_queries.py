from apps.api.app.database.queries import (
    country_vote_distribution,
    country_vote_history,
    council_vote_distribution,
    most_contested_resolutions,
)


print("\nINDIA VOTE DISTRIBUTION")
print("-" * 50)
print(country_vote_distribution("INDIA"))


print("\nSECURITY COUNCIL VOTE DISTRIBUTION")
print("-" * 50)
print(council_vote_distribution("Security Council"))


print("\nMOST CONTESTED RESOLUTIONS")
print("-" * 50)
print(
    most_contested_resolutions(10)[
        [
            "resolution_code",
            "council_name",
            "total_votes",
            "yes_votes",
            "no_votes",
            "abstain_votes",
        ]
    ]
)


print("\nINDIA VOTE HISTORY")
print("-" * 50)
india_history = country_vote_history("INDIA")

print(india_history.head(10))
print(f"Total India vote records: {len(india_history):,}")