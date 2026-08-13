from pathlib import Path

from packages.pipeline.ingestion.ga_loader import load_ga_dataset
from packages.pipeline.transformation.canonical import normalize_votes
from packages.warehouse.dimensions import (
    build_dim_body,
    build_dim_country,
    build_dim_date,
    build_dim_resolution,
)
from packages.warehouse.facts import build_fact_votes


SOURCE_PATH = Path(
    "data/raw/2026_02_06_ga_voting.csv"
)


print("Loading official GA dataset...")
source_df = load_ga_dataset(SOURCE_PATH)

print(f"Source rows: {len(source_df):,}")


print("\nApplying canonical transformation...")
canonical_df = normalize_votes(
    source_df,
    body_code="GA",
)

print(f"Canonical rows: {len(canonical_df):,}")


print("\nBuilding dimensions...")

dim_body = build_dim_body(canonical_df)
dim_country = build_dim_country(canonical_df)
dim_date = build_dim_date(canonical_df)
dim_resolution = build_dim_resolution(canonical_df)

print(f"Body rows:       {len(dim_body):,}")
print(f"Country rows:    {len(dim_country):,}")
print(f"Date rows:       {len(dim_date):,}")
print(f"Resolution rows: {len(dim_resolution):,}")


print("\nBuilding fact_votes...")

fact = build_fact_votes(
    canonical_df,
    dim_body,
    dim_date,
    dim_country,
    dim_resolution,
)

print(f"Fact rows: {len(fact):,}")


print("\nFACT SAMPLE")
print("-" * 60)

print(
    fact.head(10).to_string(index=False)
)


print("\nFACT COLUMNS")
print("-" * 60)

print(fact.columns.tolist())


print("\nFACT VALIDATION")
print("-" * 60)


# ---------------------------------------------------------
# 1. Row count
# ---------------------------------------------------------

assert len(fact) == len(canonical_df), (
    "Fact row count does not match canonical row count."
)

print("Row count validation: PASSED")


# ---------------------------------------------------------
# 2. Required columns
# ---------------------------------------------------------

expected_columns = [
    "vote_event_id",
    "body_id",
    "resolution_id",
    "country_id",
    "date_id",
    "vote_code",
    "vote_label",
    "vote_score",
]

assert fact.columns.tolist() == expected_columns, (
    "Fact columns do not match expected warehouse schema."
)

print("Column validation: PASSED")


# ---------------------------------------------------------
# 3. Null foreign keys
# ---------------------------------------------------------

foreign_keys = [
    "vote_event_id",
    "body_id",
    "resolution_id",
    "country_id",
    "date_id",
]

for column in foreign_keys:
    assert fact[column].notna().all(), (
        f"Null values found in fact key: {column}"
    )

print("Foreign-key validation: PASSED")


# ---------------------------------------------------------
# 4. Vote codes
# ---------------------------------------------------------

valid_votes = {"Y", "N", "A", "X"}

invalid_votes = (
    set(fact["vote_code"].dropna().unique())
    - valid_votes
)

assert not invalid_votes, (
    f"Invalid vote codes found: {invalid_votes}"
)

print("Vote-code validation: PASSED")


# ---------------------------------------------------------
# 5. Fact grain
# ---------------------------------------------------------

duplicate_count = fact.duplicated(
    subset=[
        "vote_event_id",
        "country_id",
    ]
).sum()

assert duplicate_count == 0, (
    f"Duplicate fact rows detected: {duplicate_count}"
)

print("Fact-grain validation: PASSED")


# ---------------------------------------------------------
# 6. Vote label consistency
# ---------------------------------------------------------

expected_labels = {
    "Y": "YES",
    "N": "NO",
    "A": "ABSTAIN",
    "X": "ABSENT",
}

for code, label in expected_labels.items():
    mask = fact["vote_code"] == code

    assert (
        fact.loc[mask, "vote_label"] == label
    ).all(), (
        f"Vote label mismatch for {code}"
    )

print("Vote-label validation: PASSED")


# ---------------------------------------------------------
# 7. Vote score consistency
# ---------------------------------------------------------

expected_scores = {
    "Y": 1.0,
    "N": -1.0,
    "A": 0.0,
}

for code, score in expected_scores.items():
    mask = fact["vote_code"] == code

    assert (
        fact.loc[mask, "vote_score"] == score
    ).all(), (
        f"Vote score mismatch for {code}"
    )

# X / ABSENT should have no score
absent_mask = fact["vote_code"] == "X"

assert fact.loc[
    absent_mask,
    "vote_score",
].isna().all(), (
    "ABSENT votes should have NULL vote_score."
)

print("Vote-score validation: PASSED")


print("\n" + "=" * 60)
print("FACT TABLE VALIDATION: PASSED")
print("=" * 60)