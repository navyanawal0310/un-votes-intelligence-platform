import pytest

from packages.analytics.query import (
    query_country_pair,
)


def test_query_country_pair():
    result = query_country_pair(
        "IND",
        "CHN",
    )

    assert result["pair"]["pair_key"] == "CHN-IND"
    assert "current_state" in result
    assert "history" in result
    assert "change_points" in result
    assert "provenance" in result


def test_query_normalizes_country_codes():
    result = query_country_pair(
        " ind ",
        " chn ",
    )

    assert result["pair"]["pair_key"] == "CHN-IND"


def test_query_supports_global_pairs():
    result = query_country_pair(
        "AFG",
        "AGO",
    )

    assert result["pair"]["pair_key"] == "AFG-AGO"


def test_query_rejects_empty_country():
    with pytest.raises(ValueError):
        query_country_pair("", "CHN")


def test_query_rejects_same_country():
    with pytest.raises(ValueError):
        query_country_pair("IND", "IND")