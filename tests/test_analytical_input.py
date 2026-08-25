from pathlib import Path

from packages.analytics.input import (
    load_analytical_input,
    validate_analytical_input,
)


GOLD_PATH = Path(
    "data/gold/country_pairs/country_pair_input.parquet"
)


def test_gold_analytical_input_exists():

    assert GOLD_PATH.exists()


def test_gold_analytical_input_loads():

    df = load_analytical_input(
        GOLD_PATH
    )

    validate_analytical_input(df)

    assert not df.empty


def test_vote_scores_are_canonical():

    df = load_analytical_input(
        GOLD_PATH
    )

    valid = df["vote_score"].dropna()
    assert valid.between(-1, 1).all()


def test_multiple_countries_exist():

    df = load_analytical_input(
        GOLD_PATH
    )

    assert df["ms_code"].nunique() > 2