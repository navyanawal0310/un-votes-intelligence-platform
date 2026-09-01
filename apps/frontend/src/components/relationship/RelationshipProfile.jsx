import { useMemo, useState } from "react";
import "./RelationshipProfile.css";
import {
  pick,
  asNumber,
  normaliseScore,
  classify,
  fileNumber,
  historyPoint,
  changeEntry,
  topicEntry,
  evidenceSummary,
  unwrapRelationship
} from "./Dossierfields";

function DossierSection({ index, eyebrow, title, children, note }) {
  return (
    <section
      className="dossier-section"
      style={{ "--reveal-delay": `${index * 140}ms` }}
    >
      <div className="dossier-section-head">
        <span className="dossier-tab">{String(index + 1).padStart(2, "0")}</span>
        <div>
          <p className="dossier-eyebrow">{eyebrow}</p>
          <h3>{title}</h3>
        </div>
        {note && <span className="dossier-note">{note}</span>}
      </div>

      <div className="dossier-section-body">{children}</div>
    </section>
  );
}

function Seal({ score }) {
  const { label, tone } = classify(score);
  const angle = score === null ? 0 : Math.max(-90, Math.min(90, (score / 100) * 90));

  return (
    <div className={`dossier-seal tone-${tone}`}>
      <svg viewBox="0 0 160 160" className="seal-dial">
        <circle cx="80" cy="80" r="70" className="seal-ring" />
        <path
          d="M 20 80 A 60 60 0 0 1 140 80"
          className="seal-arc"
          fill="none"
        />
        <line
          x1="80"
          y1="80"
          x2="80"
          y2="26"
          className="seal-needle"
          transform={`rotate(${angle} 80 80)`}
        />
        <circle cx="80" cy="80" r="5" className="seal-pivot" />
      </svg>
      <div className="seal-readout">
        <span className="seal-score">
          {score === null ? "—" : `${score > 0 ? "+" : ""}${score.toFixed(0)}`}
        </span>
        <span className="seal-label">{label}</span>
      </div>
    </div>
  );
}

function LedgerRow({ label, value, hint }) {
  if (value === null || value === undefined) return null;

  return (
    <div className="ledger-row">
      <span className="ledger-label">{label}</span>
      <span className="ledger-fill" aria-hidden="true" />
      <span className="ledger-value">
        {value}
        {hint && <em>{hint}</em>}
      </span>
    </div>
  );
}

function Timeline({ points, nameA, nameB }) {
  const usable = points.filter((p) => p.score !== null);

  if (usable.length < 2) {
    return (
      <p className="dossier-empty">
        Not enough recorded sessions to plot a trajectory yet.
      </p>
    );
  }

  const width = 640;
  const height = 200;
  const padding = 28;
  const scores = usable.map((p) => p.score);
  const min = Math.min(-100, ...scores);
  const max = Math.max(100, ...scores);

  const x = (i) =>
    padding + (i / (usable.length - 1)) * (width - padding * 2);
  const y = (s) =>
    height -
    padding -
    ((s - min) / (max - min || 1)) * (height - padding * 2);

  const path = usable
    .map((p, i) => `${i === 0 ? "M" : "L"} ${x(i).toFixed(1)} ${y(p.score).toFixed(1)}`)
    .join(" ");

  const zeroY = y(0);

  return (
    <div className="timeline-wrap">
      <svg viewBox={`0 0 ${width} ${height}`} className="timeline-svg">
        <line
          x1={padding}
          x2={width - padding}
          y1={zeroY}
          y2={zeroY}
          className="timeline-zero"
        />
        <path d={path} className="timeline-path" fill="none" />
        {usable.map((p, i) => (
          <circle
            key={`${p.label}-${i}`}
            cx={x(i)}
            cy={y(p.score)}
            r={i === usable.length - 1 ? 4.5 : 2.6}
            className="timeline-point"
          />
        ))}
        <text x={padding} y={16} className="timeline-caption">
          Positive values indicate stronger voting alignment
        </text>
      </svg>
      <div className="timeline-axis">
        <span>{usable[0].label}</span>
        <span>{usable[usable.length - 1].label}</span>
      </div>
    </div>
  );
}

function TopicBars({ topics }) {
  const usable = topics.filter((t) => t.score !== null).slice(0, 8);

  if (usable.length === 0) {
    return (
      <p className="dossier-empty">
        No topic-level breakdown is available in the current voting record.
      </p>
    );
  }

  return (
    <div className="topic-list">
      {usable.map((t, i) => {
        const width = Math.max(4, Math.min(100, (t.score + 100) / 2));

        return (
          <div className="topic-row" key={`${t.name}-${i}`}>
            <span className="topic-name">{t.name}</span>
            <div className="topic-track">
              <div
                className="topic-fill"
                style={{ width: `${width}%` }}
              />
            </div>
            <span className="topic-score">
              {t.score > 0 ? "+" : ""}
              {t.score.toFixed(0)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function TurningPoints({ entries }) {
  if (entries.length === 0) {
    return (
      <div className="turning-empty">
        <strong>No statistically significant turning point detected</strong>
        <p>
          The available voting record does not contain a persistent
          alignment shift that meets the current change-point criteria.
        </p>
      </div>
    );
  }

  return (
    <ol className="turning-points">
      {entries.slice(0, 6).map((e, i) => (
        <li key={`${e.date}-${i}`}>
          <span className="tp-date">{e.date || "Undated"}</span>
          <div className="tp-body">
            <p className="tp-title">{e.title}</p>
            {e.detail && <p className="tp-detail">{e.detail}</p>}
          </div>
          {e.magnitude !== null && (
            <span className={`tp-tag ${e.magnitude >= 0 ? "up" : "down"}`}>
              {e.magnitude >= 0 ? "▲" : "▼"} {Math.abs(e.magnitude).toFixed(2)}
            </span>
          )}
        </li>
      ))}
    </ol>
  );
}

function Interrogation({
  query,
  setQuery,
  queryResult,
  queryLoading,
  onAsk,
  nameA,
  nameB,
}) {
  return (
    <div className="interrogation">
      <form
        className="interrogation-form"
        onSubmit={(event) => {
          event.preventDefault();
          if (!query.trim() || queryLoading) return;
          onAsk();
        }}
      >
        <label htmlFor="dossier-query">
          Put a question to the record — e.g. "When did {nameA} and {nameB}{" "}
          drift apart on climate votes?"
        </label>
        <div className="interrogation-input">
          <input
            id="dossier-query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Ask the voting record a question…"
          />
          <button type="submit" disabled={queryLoading || !query.trim()}>
            {queryLoading ? "Querying…" : "Ask"}
          </button>
        </div>
      </form>

      {queryResult && (
  <div className="interrogation-transcript">
    <div className="transcript-question">
      <span>Question</span>
      <p>{queryResult.question || query}</p>
    </div>

    <div className="transcript-answer">
      <span>Analytical answer</span>
      <p>
        {queryResult.answer || "No answer returned from the analytical record."}
      </p>
    </div>

    {(queryResult.evidence ||
      queryResult.evidence_source ||
      queryResult.provenance) && (
      <div className="transcript-evidence-block">
        {queryResult.evidence && (
          <div>
            <span>Evidence</span>
            <p>{queryResult.evidence}</p>
          </div>
        )}

        {queryResult.evidence_source && (
          <div>
            <span>Source</span>
            <p>{queryResult.evidence_source}</p>
          </div>
        )}

        {queryResult.provenance && (
          <div>
            <span>Provenance</span>
            <p>{queryResult.provenance}</p>
          </div>
        )}
      </div>
    )}
  </div>
)}
    </div>
  );
}

function RelationshipProfile({
  relationship,
  history,
  changes = [],
  countryA,
  countryB,
  query = "",
  setQuery = () => {},
  queryResult,
  queryLoading = false,
  onAsk = () => {},
}) {
  const [expanded, setExpanded] = useState(false);

  const record = unwrapRelationship(relationship);

  const nameA = pick(record, ["country_a_name", "country_a"], countryA) || countryA;
  const nameB = pick(record, ["country_b_name", "country_b"], countryB) || countryB;

  const score = useMemo(
    () =>
      normaliseScore(
        pick(record, [
          "relationship_score",
          "score",
          "alignment_score",
        ])
      ),
    [relationship]
  );

  const agreementRate = asNumber(
    pick(record, ["agreement_rate", "agreement_percentage"])
  );
  const disagreementRate = asNumber(
    pick(record, ["disagreement_rate", "disagreement_percentage"])
  );
  const totalVotes = asNumber(
    pick(record, ["total_votes", "shared_votes", "vote_count"])
  );
  const sharedSessions = asNumber(
    pick(record, ["sessions", "shared_sessions", "session_count"])
  );
  const trend = pick(record, ["trend", "trajectory"], null);
  const summary = pick(
    relationship,
    ["summary", "narrative", "description"],
    null
  );

  const historyRows =
    Array.isArray(history?.history)
      ? history.history
      : Array.isArray(history?.data)
      ? history.data
      : Array.isArray(history?.trajectory)
      ? history.trajectory
      : Array.isArray(history?.history?.data)
      ? history.history.data
      : Array.isArray(history)
      ? history
      : [];
  const points = useMemo(
    () => historyRows.map(historyPoint),
    [historyRows]
  );

  const topics = useMemo(() => {
    const candidates = [
      record?.substantive_intelligence?.subject_rankings,
      record?.substantive_intelligence?.subject_trends,
      record?.evidence?.substantive?.subject_rankings,
      record?.evidence?.substantive?.subject_trends,
      record?.topics,
      record?.issues,
      record?.categories,
    ];

    const raw = candidates.find(Array.isArray);

    return Array.isArray(raw)
      ? raw.map(topicEntry)
      : [];
  }, [record]);

  const turningPoints = useMemo(() => {
    const episodes = pick(
      record,
      ["change_episodes", "changeEpisodes"],
      []
    );

    if (!Array.isArray(episodes)) {
      return [];
    }

    return episodes
      .map(changeEntry)
      .filter(Boolean);
  }, [record]);
  if (!record) return null;
  const evidence = evidenceSummary(record);

  const substantive =
    record?.substantive_intelligence ||
    record?.substantive ||
    {};

  const substantiveSummary =
    substantive?.evidence_summary ||
    substantive?.summary ||
    record?.evidence?.substantive ||
    {};

  const subjectRankings =
    Array.isArray(substantive?.subject_rankings)
      ? substantive.subject_rankings
      : [];

  const subjectTrends =
    Array.isArray(substantive?.subject_trends)
      ? substantive.subject_trends
      : [];

  const resolutionDisagreements =
    Array.isArray(substantive?.resolution_disagreements)
      ? substantive.resolution_disagreements
      : [];

  const issuePositions =
    substantive?.issue_positions || {};

  const issueRowsCountryA =
    Array.isArray(issuePositions?.[countryA])
      ? issuePositions[countryA]
      : [];

  const issueRowsCountryB =
    Array.isArray(issuePositions?.[countryB])
      ? issuePositions[countryB]
      : [];


  const directionalAgreement = asNumber(
  pick(record, [
    "directional_agreement",
    "directionalAgreement",
  ])
);

const meanAlignment = asNumber(
  pick(record, [
    "mean_alignment",
    "meanAlignment",
  ])
);

const meanDivergence = asNumber(
  pick(record, [
    "mean_divergence",
    "meanDivergence",
  ])
);

const rawChangePoints = pick(record, [
  "change_points",
  "changePoints",
], []);

const recordChangePoints = Array.isArray(rawChangePoints)
  ? rawChangePoints
  : Array.isArray(rawChangePoints?.items)
  ? rawChangePoints.items
  : Array.isArray(rawChangePoints?.records)
  ? rawChangePoints.records
  : asNumber(rawChangePoints) !== null
  ? Number(rawChangePoints)
  : [];

const changeEpisodeCount =
  asNumber(
    pick(record, [
      "change_episode_count",
      "changeEpisodeCount",
    ])
  ) ?? turningPoints.length;

const confirmedEpisodeCount =
  asNumber(
    pick(record, [
      "confirmed_episode_count",
      "confirmedEpisodeCount",
    ])
  ) ??
  turningPoints.filter(
    (point) => point.confirmed === true
  ).length;

const evidenceCount = asNumber(
  pick(record, [
    "evidence_count",
    "evidenceCount",
    "total_votes",
    "shared_votes",
  ])
);

const relationshipDirection = pick(
  record,
  [
    "relationship_direction",
    "relationshipDirection",
    "direction",
  ],
  null
);
  return (
    <article
      className="dossier"
      key={`${countryA}-${countryB}`}
    >
      <header className="dossier-header">
        <div className="dossier-header-meta">
          <span className="dossier-file">{fileNumber(countryA, countryB)}</span>
          <span className="dossier-divider" aria-hidden="true">·</span>
          <span>UN GENERAL ASSEMBLY VOTING RECORD</span>
        </div>

        <div className="dossier-header-main">
          <h2>
            {nameA}
            <span className="dossier-versus">vs</span>
            {nameB}
          </h2>

          {summary && <p className="dossier-summary">{summary}</p>}
          {!summary && (
            <p className="dossier-summary">
              A statistical read of how {nameA} and {nameB} have voted
              relative to one another across recorded General Assembly
              sessions.
            </p>
          )}
        </div>

        <Seal score={score} />
      </header>
            <div className="intelligence-strip">
        <div className="intelligence-item">
          <span>Current alignment</span>
          <strong>
            {score !== null ? `${score.toFixed(1)}%` : "—"}
          </strong>
        </div>

        <div className="intelligence-item">
          <span>Direction</span>
          <strong>
            {relationshipDirection || "—"}
          </strong>
        </div>

        <div className="intelligence-item">
          <span>Directional agreement</span>
          <strong>
            {directionalAgreement !== null
              ? `${(
                  directionalAgreement <= 1
                    ? directionalAgreement * 100
                    : directionalAgreement
                ).toFixed(1)}%`
              : "—"}
          </strong>
        </div>

        <div className="intelligence-item">
          <span>Evidence</span>
          <strong>
            {evidenceCount !== null
              ? evidenceCount.toLocaleString()
              : "—"}
          </strong>
        </div>

        <div className="intelligence-item">
          <span>Detected changes</span>
          <strong>
            {changeEpisodeCount !== null
              ? changeEpisodeCount.toLocaleString()
              : "—"}
          </strong>
        </div>
      </div>
      <div className={`dossier-body ${expanded ? "" : "is-collapsed"}`}>
        <DossierSection
          index={0}
          eyebrow="Exhibit A"
          title="Agreement vs. disagreement"
        >
        <div className="ledger">
          <LedgerRow
            label="Relationship score"
            value={score !== null ? `${score.toFixed(1)}%` : null}
          />
          <LedgerRow
            label="Relationship direction"
            value={relationshipDirection}
          />
          <LedgerRow
            label="Directional agreement"
            value={
              directionalAgreement !== null
                ? `${(directionalAgreement <= 1
                    ? directionalAgreement * 100
                    : directionalAgreement
                  ).toFixed(1)}%`
                : null
            }
          />
          <LedgerRow
            label="Mean alignment"
            value={
              meanAlignment !== null
                ? `${(meanAlignment <= 1
                    ? meanAlignment * 100
                    : meanAlignment
                  ).toFixed(1)}%`
                : null
            }
          />
          <LedgerRow
            label="Mean divergence"
            value={
              meanDivergence !== null
                ? `${(meanDivergence <= 1
                    ? meanDivergence * 100
                    : meanDivergence
                  ).toFixed(1)}%`
                : null
            }
          />
          <LedgerRow
            label="Evidence count"
            value={
              evidenceCount !== null
                ? evidenceCount.toLocaleString()
                : null
            }
          />
          <LedgerRow
            label="Detected changes"
            value={
              changeEpisodeCount !== null
                ? changeEpisodeCount.toLocaleString()
                : null
            }
          />
          <LedgerRow
            label="Confirmed changes"
            value={
              confirmedEpisodeCount !== null
                ? confirmedEpisodeCount.toLocaleString()
                : null
            }
          />
        </div>
        </DossierSection>

        <DossierSection
          index={1}
          eyebrow="Exhibit B"
          title="Historical movement"
          note={points.length ? `${points.length} data points` : null}
        >
          <Timeline points={points} nameA={nameA} nameB={nameB} />
        </DossierSection>

        <DossierSection
          index={2}
          eyebrow="Exhibit C"
          title="Issues & topic alignment"
        >
        <div className="evidence-grid">
          <div className="evidence-card">
            <span className="evidence-number">
              {evidence.subjects ?? 0}
            </span>
            <span className="evidence-label">
              Subjects analysed
            </span>
          </div>

          <div className="evidence-card">
            <span className="evidence-number">
              {evidence.subjectTrendRows ?? 0}
            </span>
            <span className="evidence-label">
              Subject trend records
            </span>
          </div>

          <div className="evidence-card">
            <span className="evidence-number">
              {evidence.resolutionDisagreements ?? 0}
            </span>
            <span className="evidence-label">
              Resolution disagreements
            </span>
          </div>

          <div className="evidence-card">
            <span className="evidence-number">
              {evidence.issueRowsCountryA ?? 0}
            </span>
            <span className="evidence-label">
              {nameA} issue records
            </span>
          </div>

          <div className="evidence-card">
            <span className="evidence-number">
              {evidence.issueRowsCountryB ?? 0}
            </span>
            <span className="evidence-label">
              {nameB} issue records
            </span>
          </div>
        </div>

          <TopicBars topics={topics} />
          <div className="substantive-note">
            <span>Analytical coverage</span>
            <p>
              {evidence.subjects ?? 0} subjects were analysed across the
              available voting record, with{" "}
              {evidence.subjectTrendRows ?? 0} subject-trend records and{" "}
              {evidence.resolutionDisagreements ?? 0} resolution-level
              disagreements available for comparison.
            </p>
          </div>

        </DossierSection>

        <DossierSection
          index={3}
          eyebrow="Exhibit D"
          title="Turning points"
          note={
            changeEpisodeCount !== null
              ? `${changeEpisodeCount} detected`
              : null
          }
        >
          <div className="turning-summary">
            <div>
              <span>Detected episodes</span>
              <strong>
                {changeEpisodeCount !== null
                  ? changeEpisodeCount.toLocaleString()
                  : "—"}
              </strong>
            </div>

            <div>
              <span>Confirmed episodes</span>
              <strong>
                {confirmedEpisodeCount !== null
                  ? confirmedEpisodeCount.toLocaleString()
                  : "—"}
              </strong>
            </div>

            <div>
              <span>Change records</span>
              <strong>
                {Array.isArray(recordChangePoints)
                  ? recordChangePoints.length
                  : recordChangePoints}
              </strong>
            </div>
          </div>
          <TurningPoints entries={turningPoints} />
        </DossierSection>
        <DossierSection
          index={4}
          eyebrow="Exhibit E"
          title="Interrogate the record"
        >
          <Interrogation
            query={query}
            setQuery={setQuery}
            queryResult={queryResult}
            queryLoading={queryLoading}
            onAsk={onAsk}
            nameA={nameA}
            nameB={nameB}
          />
        </DossierSection>
        <DossierSection
          index={5}
          eyebrow="Evidence"
          title="Evidence & method"
        >
          <div className="method-grid">
            <div>
              <span>Evidence source</span>
              <strong>
                {record.evidence_source || "UN VOTING"}
              </strong>
            </div>

            <div>
              <span>Provenance</span>
              <strong>
                {record.provenance || "UN_VOTES_ANALYZER"}
              </strong>
            </div>

            <div>
              <span>Temporal alignment</span>
              <strong>
                {record.evidence?.temporal_alignment ??
                  record.evidence_summary?.temporal_alignment ??
                  "—"}
              </strong>
            </div>

            <div>
              <span>Change points</span>
              <strong>
                {record.evidence?.change_points ??
                  record.evidence_summary?.change_points ??
                  changeEpisodeCount ??
                  "—"}
              </strong>
            </div>

            <div>
              <span>Issue attribution</span>
              <strong>
                {(
                  record.evidence?.issue_attribution ??
                  record.evidence_summary?.issue_attribution
                ) > 0
                  ? (
                      record.evidence?.issue_attribution ??
                      record.evidence_summary?.issue_attribution
                    )
                  : "Not available"}
              </strong>
            </div>

            <div>
              <span>Episode attribution</span>
              <strong>
                {(
                  record.evidence?.episode_attribution ??
                  record.evidence_summary?.episode_attribution
                ) > 0
                  ? (
                      record.evidence?.episode_attribution ??
                      record.evidence_summary?.episode_attribution
                    )
                  : "Not available"}
              </strong>
            </div>
          </div>

          <p className="method-note">
            Relationship estimates are derived from observed United Nations
            General Assembly voting behaviour. Evidence and attribution fields
            indicate how much supporting analytical evidence is available for
            this pairing.
          </p>
        </DossierSection>
      </div>

      <button
        type="button"
        className="dossier-toggle"
        onClick={() => setExpanded((v) => !v)}
      >
        {expanded ? "Collapse full file ↑" : "This is the full file ↓"}
      </button>
    </article>
  );
}

export default RelationshipProfile;