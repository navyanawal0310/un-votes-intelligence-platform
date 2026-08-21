from pathlib import Path
import pandas as pd
import numpy as np


ROOT = Path.cwd()


# ============================================================
# CONFIGURATION
# ============================================================

ALIGNMENT_FILE = ROOT / "country_pair_alignment.csv"
ISSUE_FILE = ROOT / "country_pair_alignment_by_issue.csv"
SUMMARY_FILE = ROOT / "country_pair_alignment_summary.csv"
TEMPORAL_FILE = ROOT / "country_pair_temporal_alignment.csv"
CHANGE_POINT_FILE = ROOT / "temporal_alignment_change_points.csv"
EPISODE_FILE = ROOT / "temporal_alignment_change_episodes.csv"
EXPLANATION_FILE = ROOT / "change_point_explanations.csv"

OUTPUT_FILE = ROOT / "country_pair_intelligence.csv"


# ============================================================
# HELPERS
# ============================================================

def find_file(filename):
    locations = [
        ROOT / filename,
        ROOT / "data" / filename,
        ROOT / "data" / "validation" / filename,
        ROOT / "reports" / filename,
        ROOT / "outputs" / filename,
        ROOT / "results" / filename,
    ]

    for path in locations:
        if path.exists():
            return path

    return None


def load_csv(filename, required=True):

    path = find_file(filename)

    if path is None:
        if required:
            raise FileNotFoundError(
                f"Required file not found: {filename}"
            )
        return pd.DataFrame()

    df = pd.read_csv(path)

    # Normalize column names.
    df.columns = [
        str(c).strip().lower().replace(" ", "_")
        for c in df.columns
    ]

    return df


def numeric(series):
    return pd.to_numeric(series, errors="coerce")


def pair_key(a, b):
    return (
        str(a).strip().upper(),
        str(b).strip().upper()
    )


def safe_mean(series):
    values = numeric(series).dropna()

    if len(values) == 0:
        return np.nan

    return values.mean()


def safe_median(series):
    values = numeric(series).dropna()

    if len(values) == 0:
        return np.nan

    return values.median()


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("=" * 78)
    print("COUNTRY-PAIR INTELLIGENCE")
    print("=" * 78)

    alignment = load_csv("country_pair_alignment.csv")
    issue = load_csv("country_pair_alignment_by_issue.csv")
    summary = load_csv(
        "country_pair_alignment_summary.csv",
        required=False
    )
    temporal = load_csv("country_pair_temporal_alignment.csv")
    change_points = load_csv(
        "temporal_alignment_change_points.csv",
        required=False
    )
    episodes = load_csv(
        "temporal_alignment_change_episodes.csv",
        required=False
    )
    explanations = load_csv(
        "change_point_explanations.csv",
        required=False
    )

    print(f"Alignment rows:       {len(alignment)}")
    print(f"Issue rows:           {len(issue)}")
    print(f"Temporal rows:        {len(temporal)}")
    print(f"Change points:        {len(change_points)}")
    print(f"Change episodes:      {len(episodes)}")
    print(f"Explanations:         {len(explanations)}")

    return (
        alignment,
        issue,
        summary,
        temporal,
        change_points,
        episodes,
        explanations,
    )


# ============================================================
# PAIR EXTRACTION
# ============================================================

def get_pairs(*frames):

    pairs = set()

    for df in frames:

        if df.empty:
            continue

        if "country_a" not in df.columns:
            continue

        if "country_b" not in df.columns:
            continue

        for _, row in df.iterrows():

            a = str(row["country_a"]).strip().upper()
            b = str(row["country_b"]).strip().upper()

            if a and b and a != "NAN" and b != "NAN":
                pairs.add((a, b))

    return sorted(pairs)


# ============================================================
# OVERALL ALIGNMENT
# ============================================================

def calculate_overall_alignment(pair, alignment):

    a, b = pair

    df = alignment[
        (alignment["country_a"].astype(str).str.upper() == a)
        &
        (alignment["country_b"].astype(str).str.upper() == b)
    ].copy()

    if df.empty:
        return np.nan

    if "alignment_score" in df.columns:
        return safe_mean(df["alignment_score"])

    return np.nan


# ============================================================
# HISTORICAL / RECENT ALIGNMENT
# ============================================================

def calculate_temporal_alignment(pair, temporal):

    a, b = pair

    df = temporal[
        (temporal["country_a"].astype(str).str.upper() == a)
        &
        (temporal["country_b"].astype(str).str.upper() == b)
    ].copy()

    if df.empty:
        return {
            "historical_alignment": np.nan,
            "recent_alignment": np.nan,
            "trend": "UNKNOWN",
        }

    if "mean_alignment" not in df.columns:
        return {
            "historical_alignment": np.nan,
            "recent_alignment": np.nan,
            "trend": "UNKNOWN",
        }

    df["mean_alignment"] = numeric(df["mean_alignment"])

    if "window_end" in df.columns:
        df["window_end"] = numeric(df["window_end"])
        df = df.sort_values("window_end")

    valid = df.dropna(subset=["mean_alignment"])

    if valid.empty:
        return {
            "historical_alignment": np.nan,
            "recent_alignment": np.nan,
            "trend": "UNKNOWN",
        }

    historical = valid.iloc[:max(1, len(valid) // 3)]
    recent = valid.iloc[-max(1, len(valid) // 3):]

    historical_value = historical["mean_alignment"].mean()
    recent_value = recent["mean_alignment"].mean()

    difference = recent_value - historical_value

    # Deliberately conservative threshold.
    if difference >= 0.05:
        trend = "INCREASING"
    elif difference <= -0.05:
        trend = "DECREASING"
    else:
        trend = "STABLE"

    return {
        "historical_alignment": historical_value,
        "recent_alignment": recent_value,
        "trend": trend,
    }


# ============================================================
# ISSUE PROFILE
# ============================================================

def calculate_issue_profile(pair, issue):

    a, b = pair

    df = issue[
        (issue["country_a"].astype(str).str.upper() == a)
        &
        (issue["country_b"].astype(str).str.upper() == b)
    ].copy()

    if df.empty:
        return {
            "top_aligned_issue": None,
            "top_divergent_issue": None,
            "top_aligned_score": np.nan,
            "top_divergent_score": np.nan,
        }

    if "mean_alignment" not in df.columns:
        return {
            "top_aligned_issue": None,
            "top_divergent_issue": None,
            "top_aligned_score": np.nan,
            "top_divergent_score": np.nan,
        }

    df["mean_alignment"] = numeric(df["mean_alignment"])

    df = df.dropna(subset=["mean_alignment"])

    if df.empty:
        return {
            "top_aligned_issue": None,
            "top_divergent_issue": None,
            "top_aligned_score": np.nan,
            "top_divergent_score": np.nan,
        }

    aligned = df.loc[df["mean_alignment"].idxmax()]
    divergent = df.loc[df["mean_alignment"].idxmin()]

    issue_column = "issue"

    return {
        "top_aligned_issue": (
            aligned[issue_column]
            if issue_column in df.columns
            else None
        ),
        "top_divergent_issue": (
            divergent[issue_column]
            if issue_column in df.columns
            else None
        ),
        "top_aligned_score": aligned["mean_alignment"],
        "top_divergent_score": divergent["mean_alignment"],
    }


# ============================================================
# CHANGE-POINT PROFILE
# ============================================================

def calculate_change_points(pair, change_points):

    if change_points.empty:
        return {
            "change_point_count": 0,
            "strongest_change_year": np.nan,
            "strongest_change_magnitude": np.nan,
            "strongest_effect_size": np.nan,
        }

    a, b = pair

    df = change_points[
        (
            change_points["country_a"].astype(str).str.upper() == a
        )
        &
        (
            change_points["country_b"].astype(str).str.upper() == b
        )
    ].copy()

    if df.empty:
        return {
            "change_point_count": 0,
            "strongest_change_year": np.nan,
            "strongest_change_magnitude": np.nan,
            "strongest_effect_size": np.nan,
        }

    if "change_magnitude" not in df.columns:
        return {
            "change_point_count": len(df),
            "strongest_change_year": np.nan,
            "strongest_change_magnitude": np.nan,
            "strongest_effect_size": np.nan,
        }

    df["change_magnitude"] = numeric(df["change_magnitude"])

    df = df.dropna(subset=["change_magnitude"])

    if df.empty:
        return {
            "change_point_count": 0,
            "strongest_change_year": np.nan,
            "strongest_change_magnitude": np.nan,
            "strongest_effect_size": np.nan,
        }

    strongest = df.loc[
        df["change_magnitude"].abs().idxmax()
    ]

    year = np.nan

    if "change_year" in df.columns:
        year = strongest["change_year"]

    effect = np.nan

    if "effect_size" in df.columns:
        effect = strongest["effect_size"]

    return {
        "change_point_count": len(df),
        "strongest_change_year": year,
        "strongest_change_magnitude": strongest["change_magnitude"],
        "strongest_effect_size": effect,
    }


# ============================================================
# HISTORICAL EVENT SUPPORT
# ============================================================

def calculate_event_support(pair, explanations):

    if explanations.empty:
        return {
            "event_supported_change_points": 0,
            "strongest_event": None,
            "event_support": "NONE",
        }

    if "country_a" not in explanations.columns:
        return {
            "event_supported_change_points": 0,
            "strongest_event": None,
            "event_support": "NONE",
        }

    a, b = pair

    df = explanations[
        (
            explanations["country_a"].astype(str).str.upper() == a
        )
        &
        (
            explanations["country_b"].astype(str).str.upper() == b
        )
    ].copy()

    if df.empty:
        return {
            "event_supported_change_points": 0,
            "strongest_event": None,
            "event_support": "NONE",
        }

    # Look for event-related explanatory fields.
    event_columns = [
        c for c in df.columns
        if "event" in c.lower()
    ]

    if not event_columns:
        return {
            "event_supported_change_points": 0,
            "strongest_event": None,
            "event_support": "NONE",
        }

    event_values = []

    for column in event_columns:

        for value in df[column].dropna():

            text = str(value).strip()

            if text and text.lower() not in {
                "nan",
                "none",
                "false",
                "0",
            }:
                event_values.append(text)

    if not event_values:
        return {
            "event_supported_change_points": 0,
            "strongest_event": None,
            "event_support": "NONE",
        }

    return {
        "event_supported_change_points": len(event_values),
        "strongest_event": event_values[0],
        "event_support": "TEMPORALLY_SUPPORTED",
    }


# ============================================================
# CONFIDENCE
# ============================================================

def calculate_confidence(row):

    score = 0

    # Data coverage.
    if pd.notna(row["overall_alignment"]):
        score += 1

    if pd.notna(row["historical_alignment"]):
        score += 1

    if pd.notna(row["recent_alignment"]):
        score += 1

    # Temporal evidence.
    if row["change_point_count"] > 0:
        score += 1

    # Strong change.
    if (
        pd.notna(row["strongest_change_magnitude"])
        and abs(row["strongest_change_magnitude"]) >= 0.10
    ):
        score += 1

    # Historical support.
    if row["event_supported_change_points"] > 0:
        score += 1

    if score >= 5:
        return "HIGH"

    if score >= 3:
        return "MODERATE"

    if score >= 1:
        return "LOW"

    return "INSUFFICIENT"


# ============================================================
# INTERPRETATION
# ============================================================

def generate_interpretation(row):

    pair = f"{row['country_a']}-{row['country_b']}"

    trend = row["trend"]

    text = f"{pair} shows {trend.lower()} alignment over the observed period."

    if pd.notna(row["recent_alignment"]):
        text += (
            f" Recent alignment is approximately "
            f"{row['recent_alignment']:.3f}."
        )

    if row["change_point_count"] > 0:

        year = row["strongest_change_year"]

        magnitude = row["strongest_change_magnitude"]

        if pd.notna(year) and pd.notna(magnitude):

            text += (
                f" The strongest detected temporal change occurs "
                f"around {int(year)} with magnitude "
                f"{magnitude:.3f}."
            )

    if row["event_supported_change_points"] > 0:

        text += (
            " At least one detected change has temporal association "
            "with a documented historical event."
        )

    text += (
        " This describes temporal association and alignment "
        "patterns; it does not establish causality."
    )

    return text


# ============================================================
# BUILD INTELLIGENCE TABLE
# ============================================================

def build_intelligence(
    alignment,
    issue,
    summary,
    temporal,
    change_points,
    episodes,
    explanations,
):

    pairs = get_pairs(
        alignment,
        issue,
        summary,
        temporal,
        change_points,
    )

    print()
    print(f"Country pairs evaluated: {len(pairs)}")

    records = []

    for pair in pairs:

        a, b = pair

        overall = calculate_overall_alignment(
            pair,
            alignment
        )

        temporal_profile = calculate_temporal_alignment(
            pair,
            temporal
        )

        issue_profile = calculate_issue_profile(
            pair,
            issue
        )

        cp_profile = calculate_change_points(
            pair,
            change_points
        )

        event_profile = calculate_event_support(
            pair,
            explanations
        )

        record = {
            "country_a": a,
            "country_b": b,

            "overall_alignment": overall,

            **temporal_profile,

            **issue_profile,

            **cp_profile,

            **event_profile,
        }

        records.append(record)

    result = pd.DataFrame(records)

    result["confidence"] = result.apply(
        calculate_confidence,
        axis=1
    )

    result["interpretation"] = result.apply(
        generate_interpretation,
        axis=1
    )

    return result


# ============================================================
# MAIN
# ============================================================

def main():

    (
        alignment,
        issue,
        summary,
        temporal,
        change_points,
        episodes,
        explanations,
    ) = load_data()

    result = build_intelligence(
        alignment,
        issue,
        summary,
        temporal,
        change_points,
        episodes,
        explanations,
    )

    print()
    print("=" * 78)
    print("COUNTRY-PAIR INTELLIGENCE RESULTS")
    print("=" * 78)

    display_columns = [
        "country_a",
        "country_b",
        "overall_alignment",
        "historical_alignment",
        "recent_alignment",
        "trend",
        "top_aligned_issue",
        "top_divergent_issue",
        "change_point_count",
        "strongest_change_year",
        "strongest_change_magnitude",
        "event_supported_change_points",
        "confidence",
    ]

    print(
        result[display_columns].to_string(
            index=False
        )
    )

    print()
    print("=" * 78)
    print("INTERPRETATIONS")
    print("=" * 78)

    for _, row in result.iterrows():

        print()
        print(
            f"{row['country_a']} - {row['country_b']}"
        )

        print(
            f"Confidence: {row['confidence']}"
        )

        print(
            row["interpretation"]
        )

    result.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print("=" * 78)
    print("COUNTRY-PAIR INTELLIGENCE COMPLETE")
    print("=" * 78)

    print(
        f"Saved intelligence: {OUTPUT_FILE.name}"
    )


if __name__ == "__main__":
    main()