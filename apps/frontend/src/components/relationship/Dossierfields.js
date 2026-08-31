// Flexible field helpers for the Relationship Dossier.
// Backend analytics field names may evolve; the UI should remain resilient.

export function pick(obj, keys, fallback = undefined) {
  if (!obj) return fallback;

  for (const key of keys) {
    const value = obj[key];

    if (value !== undefined && value !== null && value !== "") {
      return value;
    }
  }

  return fallback;
}

export function asNumber(value) {
  if (value === undefined || value === null || value === "") return null;

  const num = typeof value === "number" ? value : Number(value);

  return Number.isFinite(num) ? num : null;
}

export function normaliseScore(raw) {
  const num = asNumber(raw);

  if (num === null) return null;

  // 0–1 fraction
  if (Math.abs(num) <= 1) return num * 100;

  // Already percentage / -100..100
  if (Math.abs(num) <= 100) return num;

  return Math.max(-100, Math.min(100, num));
}

export function classify(score) {
  if (score === null) {
    return { label: "Insufficient record", tone: "neutral" };
  }

  if (score >= 55) return { label: "Aligned", tone: "aligned" };
  if (score >= 15) return { label: "Leaning aligned", tone: "aligned" };
  if (score > -15) return { label: "Mixed record", tone: "neutral" };
  if (score > -55) return { label: "Leaning divergent", tone: "divergent" };

  return { label: "Divergent", tone: "divergent" };
}

export function fileNumber(countryA, countryB) {
  const code = `${countryA || "XXX"}-${countryB || "XXX"}`;
  let hash = 0;

  for (let i = 0; i < code.length; i += 1) {
    hash = (hash * 31 + code.charCodeAt(i)) % 98999;
  }

  return `UNGA/${code}/${String(hash + 1000).padStart(5, "0")}`;
}

export function historyPoint(row) {
  return {
    label: pick(row, ["year", "period", "date", "label"], ""),
    score: normaliseScore(
      pick(row, [
        "score",
        "relationship_score",
        "agreement_rate",
        "agreement_score",
        "alignment",
        "value",
      ])
    ),
  };
}

export function changeEntry(row) {
  return {
    date: pick(row, ["year", "period", "date", "label"], ""),
    title: pick(
      row,
      ["title", "headline", "summary", "reason", "description"],
      "Shift in voting alignment"
    ),
    detail: pick(
      row,
      ["detail", "description", "explanation", "notes"],
      ""
    ),
    magnitude: asNumber(
      pick(row, ["magnitude", "delta", "change", "shift"])
    ),
    direction: pick(row, ["direction", "trend"], null),
  };
}

export function topicEntry(row) {
  if (typeof row === "string") {
    return {
      name: row,
      score: null,
      votes: null,
    };
  }

  return {
    name: pick(
      row,
      ["topic", "name", "issue", "category", "label", "subject"],
      "Unlabelled issue area"
    ),
    score: normaliseScore(
      pick(
        row,
        [
          "score",
          "agreement_rate",
          "alignment",
          "alignment_score",
          "value",
        ]
      )
    ),
    votes: asNumber(
      pick(row, ["votes", "count", "n", "total_votes"])
    ),
  };
}

/*
 * Backend evidence summary adapter.
 *
 * Example backend:
 * evidence_summary: {
 *   subjects: 153,
 *   subject_trend_rows: 29,
 *   resolution_disagreements: 1412,
 *   issue_rows_country_a: 276,
 *   issue_rows_country_b: 275
 * }
 */
export function evidenceSummary(obj) {
  const summary =
    obj?.evidence_summary ||
    obj?.evidenceSummary ||
    {};

  return {
    subjects: asNumber(
      pick(summary, ["subjects", "subject_count"])
    ),

    subjectTrendRows: asNumber(
      pick(summary, [
        "subject_trend_rows",
        "subject_trends",
        "trend_rows",
      ])
    ),

    resolutionDisagreements: asNumber(
      pick(summary, [
        "resolution_disagreements",
        "disagreements",
        "resolution_disagreement_count",
      ])
    ),

    issueRowsCountryA: asNumber(
      pick(summary, [
        "issue_rows_country_a",
        "country_a_issue_rows",
      ])
    ),

    issueRowsCountryB: asNumber(
      pick(summary, [
        "issue_rows_country_b",
        "country_b_issue_rows",
      ])
    ),
  };
}