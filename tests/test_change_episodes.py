import pandas as pd

from packages.analytics.temporal_change_episodes import (
    build_change_episodes,
)


def synthetic_changes():
    return pd.DataFrame(
        [
            {
                "country_a": "AAA",
                "country_b": "BBB",
                "change_year": 2000,
                "change_magnitude": 0.20,
                "effect_size": 2.0,
                "confirmed": True,
                "confidence": 0.80,
            },
            {
                "country_a": "AAA",
                "country_b": "BBB",
                "change_year": 2001,
                "change_magnitude": 0.30,
                "effect_size": 3.0,
                "confirmed": True,
                "confidence": 0.85,
            },
            {
                "country_a": "AAA",
                "country_b": "BBB",
                "change_year": 2005,
                "change_magnitude": 0.10,
                "effect_size": 1.5,
                "confirmed": False,
                "confidence": 0.60,
            },
        ]
    )


def test_nearby_changes_form_one_episode():

    episodes = build_change_episodes(
        synthetic_changes(),
        max_gap=2,
    )

    assert len(episodes) == 2

    first = episodes.iloc[0]

    assert first["episode_start"] == 2000
    assert first["episode_end"] == 2001
    assert first["detections"] == 2
    assert first["confirmed_detections"] == 2


def test_episode_peak_is_largest_change():

    episodes = build_change_episodes(
        synthetic_changes(),
        max_gap=2,
    )

    first = episodes.iloc[0]

    assert first["peak_change_year"] == 2001
    assert first["max_change_magnitude"] == 0.30


def test_episode_preserves_country_pair():

    episodes = build_change_episodes(
        synthetic_changes(),
        max_gap=2,
    )

    assert set(
        episodes["country_a"]
    ) == {"AAA"}

    assert set(
        episodes["country_b"]
    ) == {"BBB"}


def test_empty_input():

    changes = pd.DataFrame()

    episodes = build_change_episodes(changes)

    assert episodes.empty