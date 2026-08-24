"""
Build Gold analytical datasets from validated Silver data.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[3]

SILVER_GA = (
    BASE_DIR
    / "data"
    / "silver"
    / "ga"
    / "ga_voting.parquet"
)

SILVER_SC = (
    BASE_DIR
    / "data"
    / "silver"
    / "sc"
    / "sc_voting.parquet"
)

GOLD_DIR = BASE_DIR / "data" / "gold"


def load_silver(path: Path) -> pd.DataFrame:

    if not path.exists():
        raise FileNotFoundError(
            f"Silver dataset not found: {path}"
        )

    return pd.read_parquet(path)


def build_vote_level_gold(
    ga: pd.DataFrame,
    sc: pd.DataFrame,
) -> pd.DataFrame:
    """
    Combine GA and SC canonical Silver datasets.

    No analytical transformation is performed here.
    """

    columns = sorted(
        set(ga.columns) & set(sc.columns)
    )

    combined = pd.concat(
        [
            ga[columns],
            sc[columns],
        ],
        ignore_index=True,
    )

    combined["date"] = pd.to_datetime(
        combined["date"],
        errors="coerce",
    )

    combined["year"] = (
        combined["date"].dt.year
    )

    return combined


def build_country_pair_input(
    votes: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create the country-vote matrix used by
    downstream country-pair analytical modules.

    One row represents:

        resolution × country × vote
    """

    required = {
        "undl_id",
        "ms_code",
        "body_code",
        "vote_code",
        "vote_score",
        "date",
        "resolution",
    }

    missing = required - set(votes.columns)

    if missing:
        raise ValueError(
            "Gold country-pair input missing columns: "
            f"{sorted(missing)}"
        )

    result = votes[
        [
            "undl_id",
            "ms_code",
            "body_code",
            "vote_code",
            "vote_score",
            "date",
            "resolution",
        ]
    ].copy()

    result["year"] = (
        pd.to_datetime(
            result["date"],
            errors="coerce",
        ).dt.year
    )

    result = result.sort_values(
        [
            "date",
            "undl_id",
            "ms_code",
        ]
    ).reset_index(drop=True)

    return result


def write_parquet(
    df: pd.DataFrame,
    path: Path,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_parquet(
        path,
        index=False,
    )

    print(
        f"[OK] {path.name}: "
        f"{len(df):,} rows"
    )


def main() -> None:

    print("=" * 70)
    print("UN VOTES ANALYZER — GOLD BUILD")
    print("=" * 70)

    print("\nLoading Silver datasets...")

    ga = load_silver(SILVER_GA)
    sc = load_silver(SILVER_SC)

    print(
        f"GA Silver: {len(ga):,} rows"
    )

    print(
        f"SC Silver: {len(sc):,} rows"
    )

    print("\nBuilding combined vote-level Gold...")

    votes = build_vote_level_gold(
        ga,
        sc,
    )

    write_parquet(
        votes,
        GOLD_DIR
        / "votes"
        / "un_votes.parquet",
    )

    print("\nBuilding country-pair analytical input...")

    pair_input = build_country_pair_input(
        votes
    )

    write_parquet(
        pair_input,
        GOLD_DIR
        / "country_pairs"
        / "country_pair_input.parquet",
    )

    print("\nGOLD BUILD COMPLETE")

    print(
        f"Total Gold rows: {len(votes):,}"
    )

    print(
        f"Countries: "
        f"{votes['ms_code'].nunique():,}"
    )

    print(
        f"Resolutions: "
        f"{votes['undl_id'].nunique():,}"
    )

    print(
        f"Years: "
        f"{votes['year'].min()} - "
        f"{votes['year'].max()}"
    )


if __name__ == "__main__":
    main()