import pandas as pd

from pathlib import Path

from packages.pipeline.ingestion.ga_loader import load_ga_dataset
from packages.pipeline.transformation.canonical import normalize_votes


GA_PATH = Path("data/raw/2026_02_06_ga_voting.csv")


print("Loading official GA dataset...")
df = load_ga_dataset(GA_PATH)

print(f"Source rows: {len(df):,}")

print("\nApplying canonical transformation...")
canonical = normalize_votes(df, body_code="GA")

print("\nCANONICAL COLUMNS")
print(canonical.columns.tolist())

print("\nCANONICAL ROW COUNT")
print(f"{len(canonical):,}")

print("\nCANONICAL SAMPLE")
print(
    canonical[
        [
            "body_code",
            "undl_id",
            "ms_code",
            "ms_name",
            "ms_vote",
            "vote_code",
            "vote_label",
            "vote_score",
            "date",
            "resolution",
        ]
    ].head(10).to_string(index=False)
)

print("\nVOTE DISTRIBUTION")
print(
    canonical[
        ["vote_code", "vote_label"]
    ].value_counts(dropna=False)
)

print("\nVOTE SCORE DISTRIBUTION")
print(
    canonical["vote_score"]
    .value_counts(dropna=False)
    .sort_index()
)

print("\nCANONICAL VALIDATION")

assert len(canonical) == len(df)

assert canonical["body_code"].eq("GA").all()

assert canonical["vote_code"].isin(
    ["Y", "N", "A", "X"]
).all()

assert canonical["vote_label"].isin(
    ["YES", "NO", "ABSTAIN", "ABSENT"]
).all()

assert canonical["date"].notna().all()

assert canonical["undl_id"].notna().all()

assert canonical["ms_code"].notna().all()

assert canonical["resolution"].notna().all()

print("Canonical transformation validation: PASSED")