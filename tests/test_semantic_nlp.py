from packages.analytics.semantic_nlp import (
    discover_topics,
    document_topic_assignments,
    semantic_similarity,
)


def test_semantic_similarity():
    value = semantic_similarity(
        [
            "nuclear disarmament",
            "arms control",
        ],
        [
            "nuclear weapons",
            "disarmament policy",
        ],
    )

    assert value is not None
    assert 0.0 <= value <= 1.0


def test_topic_discovery():
    result = discover_topics(
        [
            "nuclear weapons disarmament",
            "nuclear arms control",
            "human rights freedom",
            "human rights protection",
            "economic development",
            "sustainable development",
        ],
        n_topics=2,
        top_words=5,
        min_df=1,
    )

    assert result["documents"] == 6
    assert len(result["topics"]) == 2


def test_document_topic_assignments():
    result = document_topic_assignments(
        [
            "nuclear weapons disarmament",
            "nuclear arms control",
            "human rights protection",
            "economic development",
        ],
        n_topics=2,
    )

    assert len(result) == 4

    for row in result:
        assert "document_index" in row
        assert "topic_id" in row
        assert "topic_score" in row