from packages.analytics.query import (
    QueryIntent,
    classify_query,
    parse_query,
)


def test_classify_relationship_profile():
    result = classify_query(
        "How aligned are India and China?"
    )

    assert result == QueryIntent.RELATIONSHIP_PROFILE


def test_classify_relationship_history():
    result = classify_query(
        "How has the India China relationship changed over time?"
    )

    assert result == QueryIntent.RELATIONSHIP_HISTORY


def test_classify_relationship_changes():
    result = classify_query(
        "When did the relationship change?"
    )

    assert result == QueryIntent.RELATIONSHIP_CHANGES


def test_classify_disagreement():
    result = classify_query(
        "Why do India and China disagree?"
    )

    assert result == QueryIntent.SUBSTANTIVE_DISAGREEMENT


def test_classify_resolution_nlp():
    result = classify_query(
        "What themes appear in their resolution text?"
    )

    assert result == QueryIntent.RESOLUTION_NLP


def test_parse_query():
    result = parse_query(
        "How aligned are India and China?",
        "ind",
        "chn",
    )

    assert result["intent"] == "RELATIONSHIP_PROFILE"
    assert result["country_a"] == "IND"
    assert result["country_b"] == "CHN"

def test_resolve_country_code():
    from packages.analytics.query import resolve_country

    assert resolve_country("IND") == "IND"
    assert resolve_country("CHN") == "CHN"


def test_resolve_country_name():
    from packages.analytics.query import resolve_country

    assert resolve_country("India") == "IND"
    assert resolve_country("China") == "CHN"


def test_resolve_country_case_insensitive():
    from packages.analytics.query import resolve_country

    assert resolve_country("india") == "IND"
    assert resolve_country("cHiNa") == "CHN"


def test_resolve_country_pair():
    from packages.analytics.query import resolve_country_pair

    pair = resolve_country_pair(
        "India",
        "China",
    )

    assert pair == ("IND", "CHN")


def test_resolve_unknown_country():
    from packages.analytics.query import resolve_country

    import pytest

    with pytest.raises(ValueError):
        resolve_country(
            "DefinitelyNotACountry"
        )

def test_execute_relationship_profile():
    from packages.analytics.query import execute_query

    result = execute_query(
        "How aligned are India and China?",
        "India",
        "China",
    )

    assert result["intent"] == "RELATIONSHIP_PROFILE"
    assert result["country_a"] == "IND"
    assert result["country_b"] == "CHN"
    assert "result" in result
    assert "provenance" in result


def test_execute_relationship_history():
    from packages.analytics.query import execute_query

    result = execute_query(
        "Show the relationship history of India and China.",
        "India",
        "China",
    )

    assert result["intent"] == "RELATIONSHIP_HISTORY"
    assert result["country_a"] == "IND"
    assert result["country_b"] == "CHN"
    assert result["result"] is not None


def test_execute_disagreement_query():
    from packages.analytics.query import execute_query

    result = execute_query(
        "Why do India and China disagree?",
        "India",
        "China",
    )

    assert result["intent"] == "SUBSTANTIVE_DISAGREEMENT"
    assert result["result"] is not None


def test_execute_resolution_nlp_query():
    from packages.analytics.query import execute_query

    result = execute_query(
        "What themes appear in their resolution text?",
        "India",
        "China",
    )

    assert result["intent"] == "RESOLUTION_NLP"
    assert result["result"] is not None

def test_execute_subject_ranking():
    from packages.analytics.query import execute_query

    result = execute_query(
        "Which subjects have the highest disagreement?",
        "India",
        "China",
    )

    assert result["intent"] == "SUBJECT_RANKING"
    assert result["country_a"] == "IND"
    assert result["country_b"] == "CHN"
    assert result["result"] is not None


def test_execute_subject_trend():
    from packages.analytics.query import execute_query

    result = execute_query(
        "Show the trend by subject over time.",
        "India",
        "China",
    )

    assert result["intent"] == "SUBJECT_TREND"
    assert result["result"] is not None


def test_execute_issue_position():
    from packages.analytics.query import execute_query

    result = execute_query(
        "What are the issue positions?",
        "India",
        "China",
    )

    assert result["intent"] == "ISSUE_POSITION"
    assert "IND" in result["result"]
    assert "CHN" in result["result"]