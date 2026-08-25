from pathlib import Path

import pandas as pd

from packages.pipeline.contracts.analytical import (
    validate_analytical_votes,
)


GOLD_PATH = Path(
    "data/gold/country_pairs/country_pair_input.parquet"
)


def test_gold_dataset_contract():

    df = pd.read_parquet(
        GOLD_PATH
    )

    validated = validate_analytical_votes(
        df
    )

    assert not validated.empty


def test_vote_scores_are_canonical():

    df = pd.read_parquet(
        GOLD_PATH
    )

    validated = validate_analytical_votes(
        df
    )

    assert validated["vote_score"].dropna().isin(
        [-1.0, 0.0, 1.0]
    ).all()


def test_required_bodies_are_valid():

    df = pd.read_parquet(
        GOLD_PATH
    )

    validated = validate_analytical_votes(
        df
    )

    assert validated["body_code"].isin(
        ["GA", "SC"]
    ).all()