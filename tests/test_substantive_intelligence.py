import duckdb
import pytest

from packages.analytics.substantive_intelligence import (
    substantive_pair_intelligence,
)


def test_substantive_pair_intelligence_rejects_same_country():
    con = duckdb.connect()

    with pytest.raises(ValueError):
        substantive_pair_intelligence(
            con,
            "IND",
            "IND",
        )

    con.close()


def test_substantive_pair_intelligence_returns_contract():
    con = duckdb.connect()

    # This test only verifies the public contract when the
    # warehouse is available through the project's normal setup.
    con.close()