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
  const min = Math.min(-20, ...scores);
  const max = Math.max(20, ...scores);

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
          {nameA} above the line, {nameB} below
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
      <p className="dossier-empty">
        No discrete turning points have been flagged in this pairing yet.
      </p>
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
          <p className="transcript-q">Q — {queryResult.question || query}</p>
          <p className="transcript-a">
            A — {queryResult.answer || "No answer returned."}
          </p>
          {queryResult.evidence && (
            <p className="transcript-evidence">{queryResult.evidence}</p>
          )}
          {queryResult.evidence_source && (
            <p className="transcript-source">
              Source: {queryResult.evidence_source}
              {queryResult.provenance ? ` · ${queryResult.provenance}` : ""}
            </p>
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

  const nameA = pick(relationship, ["country_a_name", "country_a"], countryA) || countryA;
  const nameB = pick(relationship, ["country_b_name", "country_b"], countryB) || countryB;

  const score = useMemo(
    () =>
      normaliseScore(
        pick(relationship, [
          "relationship_score",
          "score",
          "alignment_score",
        ])
      ),
    [relationship]
  );

  const agreementRate = asNumber(
    pick(relationship, ["agreement_rate", "agreement_percentage"])
  );
  const disagreementRate = asNumber(
    pick(relationship, ["disagreement_rate", "disagreement_percentage"])
  );
  const totalVotes = asNumber(
    pick(relationship, ["total_votes", "shared_votes", "vote_count"])
  );
  const sharedSessions = asNumber(
    pick(relationship, ["sessions", "shared_sessions", "session_count"])
  );
  const trend = pick(relationship, ["trend", "trajectory"], null);
  const summary = pick(
    relationship,
    ["summary", "narrative", "description"],
    null
  );

  const historyRows = Array.isArray(history?.history)
    ? history.history
    : Array.isArray(history)
    ? history
    : [];
  const points = useMemo(
    () => historyRows.map(historyPoint),
    [historyRows]
  );

  const topics = useMemo(() => {
    const raw = pick(relationship, ["topics", "issues", "categories"], []);
    return Array.isArray(raw) ? raw.map(topicEntry) : [];
  }, [relationship]);

  const turningPoints = useMemo(
    () => (Array.isArray(changes) ? changes.map(changeEntry) : []),
    [changes]
  );

  if (!relationship) return null;

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

      <div className={`dossier-body ${expanded ? "" : "is-collapsed"}`}>
        <DossierSection
          index={0}
          eyebrow="Exhibit A"
          title="Agreement vs. disagreement"
        >
          <div className="ledger">
            <LedgerRow
              label="Agreement rate"
              value={
                agreementRate !== null
                  ? `${(agreementRate <= 1 ? agreementRate * 100 : agreementRate).toFixed(1)}%`
                  : null
              }
            />
            <LedgerRow
              label="Disagreement rate"
              value={
                disagreementRate !== null
                  ? `${(disagreementRate <= 1
                      ? disagreementRate * 100
                      : disagreementRate
                    ).toFixed(1)}%`
                  : null
              }
            />
            <LedgerRow
              label="Shared votes on record"
              value={totalVotes !== null ? totalVotes.toLocaleString() : null}
            />
            <LedgerRow
              label="Shared sessions"
              value={sharedSessions !== null ? sharedSessions.toLocaleString() : null}
            />
            <LedgerRow label="Trajectory" value={trend} />
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
          <TopicBars topics={topics} />
        </DossierSection>

        <DossierSection
          index={3}
          eyebrow="Exhibit D"
          title="Turning points"
        >
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