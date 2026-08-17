from packages.warehouse.database import get_connection

from packages.analytics.bridge_swing import (
    build_voting_network,
    calculate_bridge_scores,
    calculate_alignment_change,
    identify_swing_states,
    bridge_swing_report,
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

    section("CURRENT VOTING NETWORK")

    network = build_voting_network(
        con,
        2006,
        2025,
        min_common_votes=25,
        min_agreement=70.0,
    )

    print(
        network.head(20).to_string(
            index=False
        )
    )

    print(
        f"\nNetwork edges: {len(network):,}"
    )

    # ---------------------------------------------------------
    # Bridge scores
    # ---------------------------------------------------------

    section("BRIDGE STATES")

    bridge = calculate_bridge_scores(
        network
    )

    print(
        bridge.head(20).to_string(
            index=False
        )
    )

    print(
        f"\nCountries ranked: {len(bridge):,}"
    )

    # ---------------------------------------------------------
    # Historical comparison
    # ---------------------------------------------------------

    section("ALIGNMENT CHANGE")

    previous = build_voting_network(
        con,
        1986,
        2005,
        min_common_votes=25,
        min_agreement=70.0,
    )

    current = network

    changes = calculate_alignment_change(
        previous,
        current,
    )

    print(
        changes.head(20).to_string(
            index=False
        )
    )

    # ---------------------------------------------------------
    # Swing states
    # ---------------------------------------------------------

    section("SWING STATES")

    swing = identify_swing_states(
        changes,
        threshold=10.0,
    )

    print(
        swing.head(20).to_string(
            index=False
        )
    )

    print(
        f"\nSwing states detected: "
        f"{len(swing):,}"
    )

    # ---------------------------------------------------------
    # Integrated report
    # ---------------------------------------------------------

    section("INTEGRATED BRIDGE / SWING REPORT")

    bridge_report, swing_report = (
        bridge_swing_report(
            con,
            previous_period=(1986, 2005),
            current_period=(2006, 2025),
            min_common_votes=25,
            min_agreement=70.0,
            swing_threshold=10.0,
        )
    )

    print(
        "\nTop bridge states:"
    )

    print(
        bridge_report.head(10).to_string(
            index=False
        )
    )

    print(
        "\nTop swing states:"
    )

    print(
        swing_report.head(10).to_string(
            index=False
        )
    )

    # ---------------------------------------------------------
    # Assertions
    # ---------------------------------------------------------

    assert not network.empty
    assert not bridge.empty
    assert not changes.empty

    assert (
        "bridge_score"
        in bridge.columns
    )

    assert (
        "swing_score"
        in changes.columns
    )

    assert (
        "direction"
        in changes.columns
    )

    section(
        "BRIDGE / SWING TEST COMPLETE"
    )

    print(
        "Bridge / swing test runner: PASSED"
    )

finally:
    con.close()