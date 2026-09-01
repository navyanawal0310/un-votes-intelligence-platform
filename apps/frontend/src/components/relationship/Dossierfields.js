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
  if (!row) {
    return {
      label: "",
      score: null,
    };
  }

  return {
    label: pick(
      row,
      ["year", "period", "date", "session", "label"],
      ""
    ),
    score: normaliseScore(
      pick(row, [
        "score",
        "relationship_score",
        "relationshipScore",
        "agreement_rate",
        "agreement_score",
        "alignment",
        "alignment_score",
        "value",
      ])
    ),
  };
}

export function changeEntry(row) {
  const episodeStart = pick(
    row,
    ["episode_start", "start_year", "change_year", "year"],
    ""
  );

  const episodeEnd = pick(
    row,
    ["episode_end", "end_year"],
    episodeStart
  );

  const peakYear = pick(
    row,
    ["peak_change_year", "change_year", "year"],
    episodeStart
  );

  const date =
    episodeStart !== episodeEnd
      ? `${episodeStart}–${episodeEnd}`
      : `${episodeStart}`;

  return {
    date,

    title:
      row?.issue
        ? `Shift in ${row.issue}`
        : "Shift in voting alignment",

    detail:
      row?.detections
        ? `${row.detections} change-point detections clustered into this episode. Peak change: ${peakYear}.`
        : "",

    magnitude: asNumber(
      pick(row, [
        "max_change_magnitude",
        "change_magnitude",
        "magnitude",
        "delta",
        "change",
        "shift",
      ])
    ),

    direction: pick(
      row,
      ["issue_direction", "direction", "trend"],
      null
    ),

    confirmed:
      row?.confirmed === true ||
      row?.confirmed === 1 ||
      row?.confirmed === "true" ||
      Number(row?.confirmed_detections || 0) > 0,

    confidence: asNumber(
      pick(row, [
        "max_confidence",
        "confidence",
      ])
    ),

    effectSize: asNumber(
      pick(row, [
        "max_effect_size",
        "effect_size",
        "effectSize",
      ])
    ),

    persistence: asNumber(
      pick(row, ["persistence", "episode_observations"])
    ),
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
  const root =
    obj?.relationship ||
    obj?.data?.relationship ||
    obj?.data ||
    obj ||
    {};

  const summary =
    root?.evidence_summary ||
    root?.evidenceSummary ||
    root?.evidence?.substantive ||
    root?.substantive_intelligence?.evidence_summary ||
    root?.substantive?.evidence_summary ||
    {};

  const subjects = pick(summary, ["subjects", "subject_count"]);

  const subjectTrendRows = pick(summary, [
    "subject_trend_rows",
    "subject_trends",
    "trend_rows",
  ]);

  const resolutionDisagreements = pick(summary, [
    "resolution_disagreements",
    "disagreements",
    "resolution_disagreement_count",
  ]);

  const issueRowsCountryA = pick(summary, [
    "issue_rows_country_a",
    "country_a_issue_rows",
  ]);

  const issueRowsCountryB = pick(summary, [
    "issue_rows_country_b",
    "country_b_issue_rows",
  ]);

  return {
    subjects:
      typeof subjects === "number"
        ? subjects
        : Array.isArray(root?.subjects)
        ? root.subjects.length
        : null,

    subjectTrendRows:
      typeof subjectTrendRows === "number"
        ? subjectTrendRows
        : Array.isArray(root?.subject_trends)
        ? root.subject_trends.length
        : null,

    resolutionDisagreements:
      typeof resolutionDisagreements === "number"
        ? resolutionDisagreements
        : Array.isArray(root?.resolution_disagreements)
        ? root.resolution_disagreements.length
        : null,

    issueRowsCountryA:
      typeof issueRowsCountryA === "number"
        ? issueRowsCountryA
        : Array.isArray(root?.issue_rows_country_a)
        ? root.issue_rows_country_a.length
        : null,

    issueRowsCountryB:
      typeof issueRowsCountryB === "number"
        ? issueRowsCountryB
        : Array.isArray(root?.issue_rows_country_b)
        ? root.issue_rows_country_b.length
        : null,
  };
}

export function unwrapRelationship(obj) {
  return (
    obj?.relationship ||
    obj?.data?.relationship ||
    obj?.data ||
    obj ||
    null
  );
}