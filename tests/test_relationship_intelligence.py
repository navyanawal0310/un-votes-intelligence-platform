from packages.analytics.relationship_intelligence import (
    relationship_profile,
    relationship_history,
    relationship_changes,
)


def test_global_country_pair_profile():
    """Non-benchmark country pairs must be queryable."""
    profile = relationship_profile("AFG", "AGO")

    assert profile["pair"] == "AFG-AGO"
    assert profile["pair_key"] == "AFG-AGO"
    assert profile["relationship_rows"] > 0
    assert profile["evidence_source"] == "UN_VOTING"
    assert profile["provenance"] == "UN_VOTES_ANALYZER"


def test_benchmark_country_pair_profile():
    """Benchmark pairs retain scorecard-compatible analysis."""
    profile = relationship_profile("IND", "CHN")

    assert profile["pair"] == "IND-CHN"
    assert profile["relationship_rows"] > 0
    assert profile["relationship_score"] is not None


def test_relationship_history():
    history = relationship_history("IND", "CHN")

    assert not history.empty
    assert "year" in history.columns
    assert "relationship_score" in history.columns
    assert "evidence_count" in history.columns
    assert history["year"].is_monotonic_increasing


def test_relationship_changes():
    changes = relationship_changes("IND", "CHN")

    assert isinstance(changes, type(relationship_changes("AFG", "AGO")))
    assert "change_year" in changes.columns