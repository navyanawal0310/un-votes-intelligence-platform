from pathlib import Path

import pandas as pd


GA_SILVER = Path("data/silver/ga/ga_voting.parquet")
SC_SILVER = Path("data/silver/sc/sc_voting.parquet")


REQUIRED_COLUMNS = {
    "undl_id",
    "ms_code",
    "ms_name",
    "ms_vote",
    "date",
    "resolution",
    "draft",
    "meeting",
    "subjects",
    "vote_note",
    "total_yes",
    "total_no",
    "total_abstentions",
    "total_non_voting",
    "total_ms",
    "undl_link",
    "body_code",
    "vote_code",
    "vote_label",
    "vote_score",
}


def check_dataset(path: Path, expected_body: str):
    assert path.exists(), f"Missing Silver dataset: {path}"

    df = pd.read_parquet(path)

    assert not df.empty

    assert REQUIRED_COLUMNS.issubset(df.columns)

    assert df["body_code"].eq(expected_body).all()

    assert df["undl_id"].notna().all()
    assert df["ms_code"].notna().all()
    assert df["date"].notna().all()

    valid_scores = {-1.0, 0.0, 1.0}

    observed_scores = set(
        df["vote_score"].dropna().unique()
    )

    assert observed_scores.issubset(valid_scores)

    assert (
        df["total_yes"].dropna() >= 0
    ).all()

    assert (
        df["total_no"].dropna() >= 0
    ).all()

    assert (
        df["total_abstentions"].dropna() >= 0
    ).all()

    assert (
        df["total_non_voting"].dropna() >= 0
    ).all()

    assert (
        df["total_ms"].dropna() >= 0
    ).all()

    return df


def test_ga_silver():
    df = check_dataset(
        GA_SILVER,
        "GA",
    )

    assert len(df) > 100_000


def test_sc_silver():
    df = check_dataset(
        SC_SILVER,
        "SC",
    )

    assert len(df) > 1_000


def test_vote_score_mapping():
    ga = pd.read_parquet(GA_SILVER)
    sc = pd.read_parquet(SC_SILVER)

    df = pd.concat(
        [ga, sc],
        ignore_index=True,
    )

    assert (
        df.loc[
            df["vote_code"] == "Y",
            "vote_score",
        ]
        .dropna()
        .eq(1.0)
        .all()
    )

    assert (
        df.loc[
            df["vote_code"] == "N",
            "vote_score",
        ]
        .dropna()
        .eq(-1.0)
        .all()
    )

    assert (
        df.loc[
            df["vote_code"] == "A",
            "vote_score",
        ]
        .dropna()
        .eq(0.0)
        .all()
    )