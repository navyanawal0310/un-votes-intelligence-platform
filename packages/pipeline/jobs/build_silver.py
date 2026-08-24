from pathlib import Path

from packages.pipeline.ingestion.ga_loader import load_ga_dataset
from packages.pipeline.ingestion.sc_loader import load_sc_dataset
from packages.pipeline.transformation.silver import write_silver


BASE_DIR = Path(__file__).resolve().parents[3]

GA_RAW = BASE_DIR / "data" / "raw" / "2026_02_06_ga_voting.csv"
SC_RAW = BASE_DIR / "data" / "raw" / "2026_02_06_sc_voting.csv"

GA_SILVER = BASE_DIR / "data" / "silver" / "ga" / "ga_voting.parquet"
SC_SILVER = BASE_DIR / "data" / "silver" / "sc" / "sc_voting.parquet"


def main() -> None:

    print("=" * 70)
    print("UN VOTES ANALYZER — SILVER BUILD")
    print("=" * 70)

    print("\nLoading General Assembly...")
    ga = load_ga_dataset(GA_RAW)

    print(f"GA rows: {len(ga):,}")

    write_silver(
        ga,
        GA_SILVER,
    )

    print(f"[OK] GA Silver -> {GA_SILVER}")

    print("\nLoading Security Council...")
    sc = load_sc_dataset(SC_RAW)

    print(f"SC rows: {len(sc):,}")

    write_silver(
        sc,
        SC_SILVER,
    )

    print(f"[OK] SC Silver -> {SC_SILVER}")

    print("\nSILVER BUILD COMPLETE")


if __name__ == "__main__":
    main()