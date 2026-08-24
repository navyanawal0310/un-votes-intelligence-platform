import pandas as pd
import pytest

from packages.common.country_pairs import (
    canonical_pair,
)

from packages.warehouse.country_pairs import (
    build_country_pair_registry,
)


def test_canonical_pair_is_order_independent():

    assert canonical_pair(
        "IND",
        "CHN",
    ) == canonical_pair(
        "CHN",
        "IND",
    )


def test_canonical_pair_normalizes_case():

    assert canonical_pair(
        "ind",
        "chn",
    ) == "CHN-IND"


def test_self_pair_is_rejected():

    with pytest.raises(ValueError):

        canonical_pair(
            "IND",
            "IND",
        )


def test_empty_country_is_rejected():

    with pytest.raises(ValueError):

        canonical_pair(
            "",
            "IND",
        )


def test_registry_is_canonical():

    countries = pd.DataFrame(
        {
            "country_id": [1, 2, 3],
            "ms_code": [
                "IND",
                "CHN",
                "USA",
            ],
        }
    )

    result = build_country_pair_registry(
        countries
    )

    assert len(result) == 3

    assert set(
        result["canonical_pair"]
    ) == {
        "CHN-IND",
        "IND-USA",
        "CHN-USA",
    }


def test_registry_has_unique_pairs():

    countries = pd.DataFrame(
        {
            "country_id": [1, 2],
            "ms_code": [
                "IND",
                "CHN",
            ],
        }
    )

    result = build_country_pair_registry(
        countries
    )

    assert result[
        "canonical_pair"
    ].is_unique


def test_registry_has_deterministic_ids():

    countries = pd.DataFrame(
        {
            "country_id": [1, 2, 3],
            "ms_code": [
                "IND",
                "CHN",
                "USA",
            ],
        }
    )

    first = build_country_pair_registry(
        countries
    )

    second = build_country_pair_registry(
        countries
    )

    pd.testing.assert_frame_equal(
        first,
        second,
    )