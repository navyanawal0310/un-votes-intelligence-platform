from packages.warehouse.database import get_connection

from packages.analytics.coalition_network import (
    build_voting_network,
    network_summary,
    country_network_strength,
    strongest_network_partners,
    detect_coalition_candidates,
)


def section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


con = get_connection()

try:

    # ---------------------------------------------------------
    # Build network
    # ---------------------------------------------------------

    section("UN VOTING NETWORK")

    network = build_voting_network(
        con,
        min_common_votes=100,
        min_agreement=75.0,
    )

    print(network.head(30).to_string(index=False))

    print(
        f"\nNetwork edges: {len(network):,}"
    )

    # ---------------------------------------------------------
    # Network summary
    # ---------------------------------------------------------

    section("NETWORK SUMMARY")

    summary = network_summary(network)

    print(
        summary.to_string(index=False)
    )

    # ---------------------------------------------------------
    # Country network strength
    # ---------------------------------------------------------

    section("COUNTRY NETWORK STRENGTH")

    strength = country_network_strength(
        network
    )

    print(
        strength.head(30).to_string(index=False)
    )

    # ---------------------------------------------------------
    # India network
    # ---------------------------------------------------------

    section("INDIA — NETWORK PARTNERS")

    india = strongest_network_partners(
        network,
        "IND",
        limit=20,
    )

    print(
        india.to_string(index=False)
    )

    # ---------------------------------------------------------
    # Coalition candidates
    # ---------------------------------------------------------

    section("COALITION CANDIDATES")

    coalitions = detect_coalition_candidates(
        network,
        min_members=3,
        min_internal_agreement=80.0,
    )

    print(
        coalitions.to_string(index=False)
    )

    print(
        f"\nCoalitions detected: "
        f"{len(coalitions):,}"
    )

    # ---------------------------------------------------------
    # Final
    # ---------------------------------------------------------

    section("COALITION NETWORK TEST COMPLETE")

    print(
        "Coalition network test runner: PASSED"
    )

finally:
    con.close()