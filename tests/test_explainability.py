from packages.analytics.explainability import (
    explain_relationship,
)


def test_explain_relationship_structure():
    result = explain_relationship(
        "IND",
        "CHN",
    )

    assert "assessment" in result
    assert "explanation" in result
    assert "evidence" in result
    assert "provenance" in result


def test_explain_relationship_has_trajectory():
    result = explain_relationship(
        "IND",
        "CHN",
    )

    trajectory = result[
        "assessment"
    ]["trajectory"]

    assert trajectory["available"] is True
    assert trajectory["first_year"] <= trajectory["last_year"]
    assert trajectory["first_score"] is not None
    assert trajectory["last_score"] is not None


def test_explain_relationship_has_topic_attribution():
    result = explain_relationship(
        "IND",
        "CHN",
    )

    topics = result[
        "assessment"
    ]["topic_attribution"]

    assert topics["available"] is True
    assert len(topics["subjects"]) > 0
    assert topics["top_subject"] is not None


def test_explain_relationship_has_evidence_quality():
    result = explain_relationship(
        "IND",
        "CHN",
    )

    quality = result[
        "assessment"
    ]["evidence_quality"]

    assert quality["evidence_count"] > 0
    assert quality["relationship_rows"] > 0
    assert quality["temporal_alignment_rows"] > 0
    assert quality["component_coverage"] > 0