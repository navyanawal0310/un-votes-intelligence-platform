import pandas as pd
from pathlib import Path

from packages.pipeline.ingestion.ga_loader import load_ga_dataset
from packages.pipeline.transformation.canonical import normalize_votes
from packages.warehouse.dimensions import (
    build_dim_body,
    build_dim_country,
    build_dim_date,
    build_dim_resolution,
)


GA_PATH = Path("data/raw/2026_02_06_ga_voting.csv")


print("Loading official GA dataset...")
df = load_ga_dataset(GA_PATH)

print(f"Source rows: {len(df):,}")

print("\nApplying canonical transformation...")
canonical = normalize_votes(df, body_code="GA")

print(f"Canonical rows: {len(canonical):,}")


print("\nBuilding dim_body...")
dim_body = build_dim_body(canonical)

print(dim_body.to_string(index=False))


print("\nBuilding dim_country...")
dim_country = build_dim_country(canonical)

print(
    dim_country.head(20).to_string(index=False)
)

print(f"Country dimension rows: {len(dim_country):,}")


print("\nBuilding dim_date...")
dim_date = build_dim_date(canonical)

print(
    dim_date.head(10).to_string(index=False)
)

print(f"Date dimension rows: {len(dim_date):,}")


print("\nBuilding dim_resolution...")
dim_resolution = build_dim_resolution(canonical)

print(
    dim_resolution.head(10).to_string(index=False)
)

print(
    f"Resolution dimension rows: "
    f"{len(dim_resolution):,}"
)


print("\nDIMENSION VALIDATION")
print("-" * 60)


assert dim_body["body_id"].is_unique
assert dim_body["body_code"].is_unique

assert dim_country["country_id"].is_unique
assert dim_country["ms_code"].is_unique
assert dim_country["country_name"].notna().all()

assert dim_date["date_id"].is_unique
assert dim_date["full_date"].is_unique

assert dim_resolution["resolution_id"].is_unique
assert dim_resolution["resolution_code"].is_unique


assert dim_body["body_code"].eq("GA").all()

assert dim_date["full_date"].notna().all()

assert dim_resolution[
    "resolution_code"
].notna().all()


print("Body dimension validation: PASSED")
print("Country dimension validation: PASSED")
print("Date dimension validation: PASSED")
print("Resolution dimension validation: PASSED")

print("\nALL DIMENSIONS VALIDATED: PASSED")