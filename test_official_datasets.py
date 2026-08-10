from pathlib import Path

from packages.pipeline.ingestion.ga_loader import load_ga_dataset
from packages.pipeline.ingestion.sc_loader import load_sc_dataset

from packages.pipeline.validation.ga_validator import validate_ga_dataset
from packages.pipeline.validation.sc_validator import validate_sc_dataset


GA_PATH = Path("data/raw/2026_02_06_ga_voting.csv")
SC_PATH = Path("data/raw/2026_02_06_sc_voting.csv")


print("Loading General Assembly...")
ga = load_ga_dataset(GA_PATH)

validate_ga_dataset(ga)

print(f"GA rows: {len(ga):,}")
print()


print("Loading Security Council...")
sc = load_sc_dataset(SC_PATH)

validate_sc_dataset(sc)

print(f"SC rows: {len(sc):,}")
print()


print("=" * 60)
print("OFFICIAL UN DATASET VALIDATION: PASSED")
print("=" * 60)