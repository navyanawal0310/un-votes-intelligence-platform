from pathlib import Path

from packages.pipeline.ingestion.ga_loader import load_ga_dataset
from packages.pipeline.validation.ga_validator import validate_ga_dataset


GA_PATH = Path("data/raw/2026_02_06_ga_voting.csv")


print("Loading official General Assembly dataset...")
df = load_ga_dataset(GA_PATH)

print(f"Rows loaded: {len(df):,}")

print("\nRunning GA validator...")
validate_ga_dataset(df)

print("\n" + "=" * 60)
print("OFFICIAL UN GENERAL ASSEMBLY VALIDATION: PASSED")
print("=" * 60)