"""Simple event-conditioned validation for UN Votes Analyzer.

Validation only: historical events do not create or tune change points.
Core rule: meaningful event signal iff abs(event_mean - pre_event_mean) >= 0.10.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
GROUND_TRUTH = ROOT / "data" / "validation" / "temporal_ground_truth.csv"
ALIGNMENT = ROOT / "country_pair_alignment.csv"
CHANGE_POINTS = ROOT / "temporal_alignment_change_points.csv"
OUTPUT = ROOT / "temporal_event_conditioned_detection.csv"

SHIFT_THRESHOLD = 0.10
CP_TOLERANCE = 5
PRE_YEARS = 3


def pair(a, b):
    return tuple(sorted((str(a).strip(), str(b).strip())))


def load_ground_truth():
    df = pd.read_csv(GROUND_TRUTH)
    required = {"country_a", "country_b", "event_start", "event_end",
                "event_name", "expected_direction"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Ground truth missing columns: {missing}")
    df["event_start"] = pd.to_numeric(df["event_start"], errors="coerce")
    df["event_end"] = pd.to_numeric(df["event_end"], errors="coerce")
    if df[["event_start", "event_end"]].isna().any().any():
        raise ValueError("Ground truth contains missing event_start/event_end values.")
    df["event_start"] = df["event_start"].astype(int)
    df["event_end"] = df["event_end"].astype(int)
    return df


def load_alignment():
    df = pd.read_csv(ALIGNMENT)
    required = {"country_a", "country_b", "year", "alignment_score"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Alignment missing columns: {missing}")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["alignment_score"] = pd.to_numeric(df["alignment_score"], errors="coerce")
    df = df.dropna(subset=["year", "alignment_score"]).copy()
    df["year"] = df["year"].astype(int)
    df["pair"] = [pair(a, b) for a, b in zip(df.country_a, df.country_b)]
    return df.groupby(["pair", "year"], as_index=False)["alignment_score"].mean()


def load_change_points():
    if not CHANGE_POINTS.exists():
        return pd.DataFrame(columns=["pair", "change_year"])
    df = pd.read_csv(CHANGE_POINTS)
    if "change_year" not in df.columns:
        return pd.DataFrame(columns=["pair", "change_year"])
    df["change_year"] = pd.to_numeric(df["change_year"], errors="coerce")
    df = df.dropna(subset=["change_year"]).copy()
    if not {"country_a", "country_b"}.issubset(df.columns):
        return pd.DataFrame(columns=["pair", "change_year"])
    df["pair"] = [pair(a, b) for a, b in zip(df.country_a, df.country_b)]
    return df[["pair", "change_year"]].assign(change_year=lambda x: x.change_year.astype(int))


def nearest_cp(cp, p, start, end):
    x = cp[cp.pair == p]
    if x.empty:
        return np.nan, np.nan, False
    vals = []
    for year in x.change_year:
        year = int(year)
        distance = 0 if start <= year <= end else min(abs(year-start), abs(year-end))
        vals.append((distance, year))
    distance, year = min(vals)
    return year, distance, distance <= CP_TOLERANCE


def analyze(event, alignment, cp):
    a, b = str(event.country_a), str(event.country_b)
    p = pair(a, b)
    start, end = int(event.event_start), int(event.event_end)
    x = alignment[alignment.pair == p]
    pre = x[(x.year >= start-PRE_YEARS) & (x.year < start)]
    during = x[(x.year >= start) & (x.year <= end)]
    pre_mean = pre.alignment_score.mean()
    event_mean = during.alignment_score.mean()
    shift = event_mean - pre_mean if pd.notna(pre_mean) and pd.notna(event_mean) else np.nan
    signal = bool(pd.notna(shift) and abs(shift) >= SHIFT_THRESHOLD)
    expected = float(event.expected_direction)
    direction = np.nan if not signal or expected == 0 else bool(np.sign(shift) == np.sign(expected))
    cp_year, cp_distance, cp_near = nearest_cp(cp, p, start, end)
    if pd.isna(shift):
        classification = "NO_DATA"
    elif not signal:
        classification = "WEAK_SIGNAL"
    elif direction is True:
        classification = "SIGNAL_DETECTED"
    else:
        classification = "SIGNAL_WRONG_DIRECTION"
    return {
        "country_a": a, "country_b": b, "event_start": start, "event_end": end,
        "event_name": event.event_name, "expected_direction": expected,
        "pre_observations": len(pre), "event_observations": len(during),
        "pre_event_mean": pre_mean, "event_mean": event_mean, "event_shift": shift,
        "meaningful_signal": signal, "direction_match": direction,
        "nearest_change_point_year": cp_year, "change_point_distance": cp_distance,
        "change_point_within_5y": cp_near, "classification": classification,
    }


def main():
    print("=" * 72)
    print("SIMPLE EVENT-CONDITIONED VALIDATION")
    print("=" * 72)
    gt = load_ground_truth()
    alignment = load_alignment()
    cp = load_change_points()
    print(f"Events evaluated: {len(gt)}")
    print(f"Alignment observations: {len(alignment)}")
    print(f"Existing change points: {len(cp)}")
    print(f"Meaningful shift threshold: {SHIFT_THRESHOLD:.2f}")

    results = pd.DataFrame([analyze(e, alignment, cp) for _, e in gt.iterrows()])
    results.to_csv(OUTPUT, index=False)

    measurable = results[results.event_shift.notna()]
    signals = measurable[measurable.meaningful_signal]
    correct = signals[signals.direction_match == True]
    cp_near = results[results.change_point_within_5y]

    print("\nEVENT RESULTS")
    cols = ["country_a", "country_b", "event_start", "event_name", "event_shift",
            "meaningful_signal", "direction_match", "nearest_change_point_year",
            "change_point_distance", "classification"]
    display = results[cols].copy()
    display["event_shift"] = display.event_shift.round(3)
    print(display.to_string(index=False))

    print("\n" + "=" * 72)
    print("VALIDATION SUMMARY")
    print("=" * 72)
    print(f"Events evaluated: {len(results)}")
    print(f"Measurable shifts: {len(measurable)}")
    print(f"Meaningful signals: {len(signals)}")
    print(f"Correct-direction signals: {len(correct)}")
    print(f"Change points within +/-5 years: {len(cp_near)}")
    if not measurable.empty:
        print(f"Mean absolute event shift: {measurable.event_shift.abs().mean():.3f}")
        print(f"Median absolute event shift: {measurable.event_shift.abs().median():.3f}")
    if not signals.empty:
        print(f"Directional agreement among signals: {signals.direction_match.mean():.3f}")
    print(f"Saved: {OUTPUT.name}")
    print("SIMPLE EVENT-CONDITIONED VALIDATION COMPLETE")


if __name__ == "__main__":
    main()
