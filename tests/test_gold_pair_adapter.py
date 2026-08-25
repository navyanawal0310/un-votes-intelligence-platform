from pathlib import Path

from packages.analytics.gold_adapter import (
    load_country_pair,
)


GOLD_PATH = Path(
    "data/gold/country_pairs/country_pair_input.parquet"
)


def test_ind_china():

    df = load_country_pair(
        GOLD_PATH,
        "IND",
        "CHN",
    )

    assert not df.empty
    assert (df["pair"] == "CHN-IND").all()


def test_reverse_orientation():

    df = load_country_pair(
        GOLD_PATH,
        "CHN",
        "IND",
    )

    assert not df.empty
    assert (df["pair"] == "CHN-IND").all()


def test_ind_russia():

    df = load_country_pair(
        GOLD_PATH,
        "IND",
        "RUS",
    )

    assert not df.empty
    assert (df["pair"] == "IND-RUS").all()


def test_usa_russia():

    df = load_country_pair(
        GOLD_PATH,
        "USA",
        "RUS",
    )

    assert not df.empty
    assert (df["pair"] == "RUS-USA").all()


def test_scores_are_canonical():

    df = load_country_pair(
        GOLD_PATH,
        "IND",
        "USA",
    )

    assert df["vote_score_a"].isin(
        [-1.0, 0.0, 1.0]
    ).all()

    assert df["vote_score_b"].isin(
        [-1.0, 0.0, 1.0]
    ).all()