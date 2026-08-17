from packages.warehouse.database import get_connection

from packages.analytics.coalition_temporal import (
    build_temporal_network,
    extract_coalitions,
    coalition_similarity,
    coalition_membership_changes,
    temporal_coalition_report,
)


def section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


con = get_connection()

try:

    periods = [
        (1946, 1965),
        (1966, 1985),
        (1986, 2005),
        (2006, 2025),
    ]

    # ---------------------------------------------------------
    # Test one temporal network
    # ---------------------------------------------------------

    section("TEMPORAL NETWORK")

    network = build_temporal_network(
        con,
        2006,
        2025,
        min_common_votes=25,
        min_agreement=75.0,
    )

    print(
        network.head(20).to_string(
            index=False
        )
    )

    print(
        f"\nEdges returned: {len(network):,}"
    )

    # ---------------------------------------------------------
    # Coalition extraction
    # ---------------------------------------------------------

    section("COALITIONS")

    coalitions = extract_coalitions(
        network,
        min_members=3,
    )

    print(
        f"Coalitions detected: {len(coalitions):,}"
    )

    for i, coalition in enumerate(
        coalitions[:10],
        start=1,
    ):
        print(
            f"{i}: "
            f"{', '.join(sorted(coalition))}"
        )

    # ---------------------------------------------------------
    # Membership similarity
    # ---------------------------------------------------------

    section("COALITION MEMBERSHIP TEST")

    similarity = coalition_similarity(
        {"IND", "LKA", "BGD"},
        {"IND", "LKA", "MYS"},
    )

    print(
        f"Example Jaccard similarity: "
        f"{similarity:.2f}%"
    )

    changes = coalition_membership_changes(
        {"IND", "LKA", "BGD"},
        {"IND", "LKA", "MYS"},
    )

    print("\nMembership changes:")
    print(changes)

    # ---------------------------------------------------------
    # Full temporal report
    # ---------------------------------------------------------

    section("TEMPORAL COALITION REPORT")

    report = temporal_coalition_report(
        con,
        periods,
        min_common_votes=25,
        min_agreement=75.0,
        min_members=3,
    )

    print(
        report.head(30).to_string(
            index=False
        )
    )

    print(
        f"\nReport rows: {len(report):,}"
    )

    section("TEMPORAL COALITION TEST COMPLETE")

    print(
        "Temporal coalition test runner: PASSED"
    )

finally:
    con.close()