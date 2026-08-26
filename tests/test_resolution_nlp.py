from packages.analytics.resolution_nlp import pair_resolution_nlp
from packages.warehouse.database import get_connection


def test_pair_resolution_nlp_returns_structure():
    con = get_connection()

    result = pair_resolution_nlp(
        con,
        "IND",
        "CHN",
    )

    assert "pair" in result
    assert "keywords" in result
    assert "resolutions" in result
    assert "evidence_source" in result
    assert "provenance" in result

    # Day-4 NLP contract
    assert "semantic_similarity" in result
    assert "topic_analysis" in result
    assert "themes" in result
    assert "nlp_methodology" in result

    con.close()


def test_pair_resolution_nlp_has_semantic_layer():
    con = get_connection()

    result = pair_resolution_nlp(
        con,
        "IND",
        "CHN",
    )

    assert "semantic_similarity" in result
    assert "topic_analysis" in result
    assert "themes" in result
    assert "nlp_methodology" in result

    assert (
        result["nlp_methodology"]["keyword_method"]
        == "TF_IDF"
    )

    assert (
        result["nlp_methodology"]["topic_method"]
        == "NMF"
    )

    assert (
        result["nlp_methodology"]["similarity_method"]
        == "TF_IDF_COSINE"
    )

    assert (
        result["nlp_methodology"]["theme_method"]
        == "RULE_BASED"
    )

    assert result["disagreement_resolutions"] >= 0
    assert result["agreement_resolutions"] >= 0

    con.close()