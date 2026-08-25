from packages.analytics.country_pair_report import (
    build_country_pair_report,
)


def test_country_pair_report_benchmark():
    report = build_country_pair_report(
        "IND",
        "CHN",
    )

    assert report["schema_version"] == "1.0"
    assert report["pair"]["pair_key"] == "CHN-IND"

    assert (
        report["current_state"]["relationship_score"]
        is not None
    )

    assert (
        report["provenance"]["evidence_source"]
        == "UN_VOTING"
    )


def test_country_pair_report_global_pair():
    report = build_country_pair_report(
        "AFG",
        "AGO",
    )

    assert report["pair"]["pair_key"] == "AFG-AGO"
    assert report["current_state"]["relationship_score"] is not None


def test_future_evidence_integration_point():
    report = build_country_pair_report(
        "IND",
        "CHN",
    )

    assert "external_evidence" in report
    assert report["external_evidence"] == []

    assert "future_sources" in report
    assert "current_affairs" in report["future_sources"]
    assert "geopolitical_events" in report["future_sources"]
    assert "speeches" in report["future_sources"]