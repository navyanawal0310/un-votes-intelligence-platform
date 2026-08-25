from __future__ import annotations

from pathlib import Path

import pandas as pd

from packages.common.country_pairs import canonical_pair


REQUIRED_COLUMNS = {
    "undl_id",
    "ms_code",
    "body_code",
    "vote_code",
    "vote_score",
    "date",
    "resolution",
    "year",
}


def load_gold_votes(path: Path) -> pd.DataFrame:
    """Load the canonical Gold voting dataset."""

    if not path.exists():
        raise FileNotFoundError(
            f"Gold dataset not found: {path}"
        )

    df = pd.read_parquet(path)

    missing = REQUIRED_COLUMNS - set(df.columns)

    if missing:
        raise ValueError(
            f"Gold dataset missing required columns: "
            f"{sorted(missing)}"
        )

    df = df.copy()

    df["ms_code"] = (
        df["ms_code"]
        .astype("string")
        .str.upper()
        .str.strip()
    )

    df["body_code"] = (
        df["body_code"]
        .astype("string")
        .str.upper()
        .str.strip()
    )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df["vote_score"] = pd.to_numeric(
        df["vote_score"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "undl_id",
            "ms_code",
            "year",
        ]
    )

    df["year"] = df["year"].astype("int16")

    return df


def load_country(
    path: Path,
    country_code: str,
) -> pd.DataFrame:
    """
    Load only one country's voting records.

    Uses Parquet filtering so the entire Gold dataset
    does not need to be loaded for pair analysis.
    """

    country_code = (
        str(country_code)
        .upper()
        .strip()
    )

    columns = [
        "undl_id",
        "ms_code",
        "body_code",
        "resolution",
        "year",
        "vote_score",
    ]

    df = pd.read_parquet(
        path,
        columns=columns,
        filters=[
            ("ms_code", "==", country_code)
        ],
    )

    if df.empty:
        raise ValueError(
            f"No voting records found for "
            f"country: {country_code}"
        )

    df["vote_score"] = pd.to_numeric(
        df["vote_score"],
        errors="coerce",
    )

    df = df[
        df["vote_score"].isin(
            [-1.0, 0.0, 1.0]
        )
    ].copy()

    return df


def prepare_pair_votes(
    df: pd.DataFrame,
    country_a: str | None = None,
    country_b: str | None = None,
) -> pd.DataFrame:
    """
    Prepare country-pair observations.

    If country_a and country_b are supplied, only that
    pair is produced.

    If omitted, the function can operate on an already
    filtered DataFrame containing multiple countries.
    """

    required = {
        "undl_id",
        "ms_code",
        "body_code",
        "resolution",
        "year",
        "vote_score",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Pair input missing columns: "
            f"{sorted(missing)}"
        )

    if country_a is None or country_b is None:
        raise ValueError(
            "country_a and country_b are required "
            "for pair analysis."
        )

    pair = canonical_pair(
        country_a,
        country_b,
    )

    left_code, right_code = pair.split("-")

    base = df[
        df["ms_code"].isin(
            [left_code, right_code]
        )
    ][
        [
            "undl_id",
            "ms_code",
            "body_code",
            "resolution",
            "year",
            "vote_score",
        ]
    ].copy()

    base = base[
        base["vote_score"].isin(
            [-1.0, 0.0, 1.0]
        )
    ]

    base = base.drop_duplicates(
        subset=[
            "undl_id",
            "ms_code",
            "body_code",
        ],
        keep="first",
    )

    left = base[
        base["ms_code"] == left_code
    ].rename(
        columns={
            "vote_score": "vote_score_a"
        }
    )

    right = base[
        base["ms_code"] == right_code
    ].rename(
        columns={
            "vote_score": "vote_score_b"
        }
    )

    merge_keys = [
        "undl_id",
        "body_code",
        "resolution",
        "year",
    ]

    result = left.merge(
        right,
        on=merge_keys,
        how="inner",
        sort=False,
    )

    result["country_a"] = left_code
    result["country_b"] = right_code
    result["pair"] = pair

    return result[
        [
            "undl_id",
            "year",
            "body_code",
            "resolution",
            "country_a",
            "country_b",
            "pair",
            "vote_score_a",
            "vote_score_b",
        ]
    ].reset_index(drop=True)


def load_country_pair(
    path: Path,
    country_a: str,
    country_b: str,
) -> pd.DataFrame:
    """
    Efficiently load and construct observations for
    any requested UN country pair.

    This is the preferred production interface.
    """

    pair = canonical_pair(
        country_a,
        country_b,
    )

    left_code, right_code = pair.split("-")

    columns = [
        "undl_id",
        "ms_code",
        "body_code",
        "resolution",
        "year",
        "vote_score",
    ]

    df = pd.read_parquet(
        path,
        columns=columns,
        filters=[
            (
                "ms_code",
                "in",
                [left_code, right_code],
            )
        ],
    )

    return prepare_pair_votes(
        df,
        left_code,
        right_code,
    )