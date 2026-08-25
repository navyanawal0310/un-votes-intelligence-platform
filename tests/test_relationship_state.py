import pandas as pd
import pytest

from packages.analytics.relationship_state import (
    build_relationship_state,
)


def base_alignment():
    return pd.DataFrame([
        {
            "country_a": "IND",
            "country_b": "CHN",
            "year": 2020,
            "mean_alignment": 0.80,
            "mean_divergence": 0.20,
            "directional_agreement": 0.75,
            "observations": 100,
        }
    ])


def test_relationship_state_builds():
    result = build_relationship_state(base_alignment())

    assert len(result) == 1
    assert result.iloc[0]["country_a"] == "IND"
    assert result.iloc[0]["country_b"] == "CHN"
    assert 0 <= result.iloc[0]["relationship_score"] <= 1


def test_relationship_direction():
    result = build_relationship_state(base_alignment())

    assert result.iloc[0]["relationship_direction"] == "ALIGNED"


def test_divergent_relationship():
    df = base_alignment()

    df.loc[0, "mean_alignment"] = 0.10
    df.loc[0, "directional_agreement"] = 0.20

    result = build_relationship_state(df)

    assert result.iloc[0]["relationship_direction"] == "DIVERGENT"


def test_episode_evidence():
    episodes = pd.DataFrame([
        {
            "country_a": "IND",
            "country_b": "CHN",
            "episode_start": 2019,
            "episode_end": 2021,
            "confirmed_detections": 2,
        }
    ])

    result = build_relationship_state(
        base_alignment(),
        episodes,
    )

    assert result.iloc[0]["change_episode_count"] == 1
    assert result.iloc[0]["confirmed_episode_count"] == 1


def test_missing_columns_fail():
    with pytest.raises(ValueError):
        build_relationship_state(
            pd.DataFrame([
                {
                    "country_a": "IND",
                    "country_b": "CHN",
                    "year": 2020,
                }
            ])
        )