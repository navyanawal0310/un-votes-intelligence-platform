import React, { useRef, useState } from "react";
import "./About.architecture.css";

// Terminology mirrors what's already used elsewhere on this page (section
// 02's flow, section 03's capabilities, section 05's innovations) and the
// backend modules that back them — nothing here is invented.
const ARCHITECTURE_LAYERS = [
  {
    id: "data",
    number: "01",
    label: "Data Foundation",
    tagline: "UN Voting Evidence",
    description:
      "The raw record of United Nations General Assembly votes — the foundation every downstream analysis is derived from.",
    input: "UN General Assembly voting records",
    output: "Canonical evidence, ready for the analytical pipeline",
    components: ["UN Voting Evidence"],
  },
  {
    id: "pipeline",
    number: "02",
    label: "Analytical Pipeline",
    tagline: "Canonical Analytical Layer",
    description:
      "Transforms raw voting evidence into a canonical analytical layer the rest of the system can query consistently.",
    input: "Canonical evidence",
    output: "A queryable analytical pipeline of countries and positions",
    components: ["load_pipeline", "available_countries"],
  },
  {
    id: "relationship",
    number: "03",
    label: "Relationship Intelligence",
    tagline: "Country-pair relationship intelligence",
    description:
      "Computes how two countries' voting behaviour compares — the relationship profile and historical trajectory behind every dossier.",
    input: "Analytical pipeline output for a country pair",
    output: "Relationship profile and historical trajectory",
    components: ["relationship_profile", "relationship_history"],
  },
  {
    id: "change",
    number: "04",
    label: "Change Detection",
    tagline: "Change-Point Detection & Temporal Episodes",
    description:
      "Identifies periods where voting alignment changes materially, then groups nearby change-points into higher-level temporal episodes.",
    input: "Relationship history over time",
    output: "Change points grouped into temporal episodes",
    components: ["relationship_changes"],
  },
  {
    id: "evidence",
    number: "05",
    label: "Evidence & Attribution",
    tagline: "Substantive, provenance-aware evidence",
    description:
      "Connects relationship analysis back to resolution and issue-level evidence, and attaches provenance to every analytical output.",
    input: "Relationship analysis and underlying voting evidence",
    output: "Evidence summaries with source and provenance",
    components: ["evidence_summary", "evidence_source", "provenance"],
  },
  {
    id: "interface",
    number: "06",
    label: "Intelligence Interface",
    tagline: "Intelligence Services → Interactive Dossiers",
    description:
      "Exposes the analysis through intelligence services and natural-language interrogation, surfaced as interactive dossiers.",
    input: "Relationship intelligence and natural-language questions",
    output: "Interactive dossier views and query answers",
    components: ["execute_query", "Interactive Dossiers"],
  },
];

function ArchitectureExplorer() {
  const [selectedId, setSelectedId] = useState(ARCHITECTURE_LAYERS[0].id);
  const buttonRefs = useRef([]);

  const activeIndex = ARCHITECTURE_LAYERS.findIndex(
    (layer) => layer.id === selectedId
  );
  const activeLayer = ARCHITECTURE_LAYERS[activeIndex];

  function focusAndSelect(nextIndex) {
    const wrapped =
      (nextIndex + ARCHITECTURE_LAYERS.length) % ARCHITECTURE_LAYERS.length;

    setSelectedId(ARCHITECTURE_LAYERS[wrapped].id);
    buttonRefs.current[wrapped]?.focus();
  }

  function handleKeyDown(event, index) {
    switch (event.key) {
      case "ArrowDown":
        event.preventDefault();
        focusAndSelect(index + 1);
        break;
      case "ArrowUp":
        event.preventDefault();
        focusAndSelect(index - 1);
        break;
      case "Home":
        event.preventDefault();
        focusAndSelect(0);
        break;
      case "End":
        event.preventDefault();
        focusAndSelect(ARCHITECTURE_LAYERS.length - 1);
        break;
      default:
        break;
    }
  }

  return (
    <div className="arch-explorer">
      <div
        className="arch-pipeline"
        role="tablist"
        aria-orientation="vertical"
        aria-label="Architecture layers"
      >
        {ARCHITECTURE_LAYERS.map((layer, index) => (
          <div className="arch-node" key={layer.id}>
            <button
              type="button"
              ref={(el) => {
                buttonRefs.current[index] = el;
              }}
              role="tab"
              id={`arch-tab-${layer.id}`}
              aria-selected={layer.id === selectedId}
              aria-controls={`arch-panel-${layer.id}`}
              tabIndex={layer.id === selectedId ? 0 : -1}
              className={
                layer.id === selectedId
                  ? "arch-layer-btn is-active"
                  : "arch-layer-btn"
              }
              onClick={() => setSelectedId(layer.id)}
              onKeyDown={(event) => handleKeyDown(event, index)}
            >
              <span className="arch-number">{layer.number}</span>
              <span className="arch-label">
                <strong>{layer.label}</strong>
                <em>{layer.tagline}</em>
              </span>
            </button>

            {index < ARCHITECTURE_LAYERS.length - 1 && (
              <span className="arch-connector" aria-hidden="true" />
            )}
          </div>
        ))}
      </div>

      <div
        className="arch-panel"
        role="tabpanel"
        id={`arch-panel-${activeLayer.id}`}
        aria-labelledby={`arch-tab-${activeLayer.id}`}
        key={activeLayer.id}
      >
        <span className="arch-panel-eyebrow">
          {activeLayer.number} — {activeLayer.label}
        </span>

        <h3>{activeLayer.tagline}</h3>

        <p className="arch-panel-description">{activeLayer.description}</p>

        <dl className="arch-panel-io">
          <div>
            <dt>Input</dt>
            <dd>{activeLayer.input}</dd>
          </div>
          <div>
            <dt>Output</dt>
            <dd>{activeLayer.output}</dd>
          </div>
        </dl>

        <div className="arch-panel-components">
          <span>Components</span>
          <ul>
            {activeLayer.components.map((component) => (
              <li key={component}>
                <code>{component}</code>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default function About() {
  return (
    <main className="about-page">
      <section className="about-hero">
        <div className="about-kicker">ABOUT THE PROJECT</div>

        <h1>
          From voting records
          <br />
          to relationship intelligence.
        </h1>

        <p>
          UN Votes Intelligence transforms United Nations General Assembly
          voting records into an analytical system for understanding how
          countries align, diverge, and change over time.
        </p>
      </section>

      <section className="about-section">
        <div className="about-label">01 — THE PROBLEM</div>

        <div className="about-content">
          <h2>Voting records tell us what happened.</h2>

          <p>
            Conventional UN voting analysis can tell us whether a country
            voted Yes, No, Abstain, or was absent on a resolution.
          </p>

          <p>
            But a much more useful question is what those individual votes
            reveal about the evolving relationship between countries.
          </p>

          <div className="statement">
            <span>THE QUESTION</span>
            <strong>
              How does voting behaviour reveal alignment,
              divergence and change over time?
            </strong>
          </div>
        </div>
      </section>

      <section className="about-section">
        <div className="about-label">02 — THE APPROACH</div>

        <div className="about-content">
          <h2>From individual votes to country-pair intelligence.</h2>

          <div className="architecture-flow">
            <div>UN VOTING DATA</div>
            <span>↓</span>
            <div>CANONICAL EVIDENCE</div>
            <span>↓</span>
            <div>ANALYTICAL PIPELINE</div>
            <span>↓</span>
            <div>RELATIONSHIP INTELLIGENCE</div>
            <span>↓</span>
            <div>INTERACTIVE DOSSIER</div>
          </div>
        </div>
      </section>

      <section className="about-section">
        <div className="about-label">03 — WHAT THE SYSTEM ANALYSES</div>

        <div className="about-content">
          <div className="feature-grid">
            <article>
              <span>01</span>
              <h3>Relationship Alignment</h3>
              <p>
                Measures the degree to which two countries exhibit similar
                voting behaviour.
              </p>
            </article>

            <article>
              <span>02</span>
              <h3>Historical Trajectory</h3>
              <p>
                Examines how the relationship evolves across the available
                voting record.
              </p>
            </article>

            <article>
              <span>03</span>
              <h3>Change-Point Detection</h3>
              <p>
                Identifies periods where voting alignment changes materially.
              </p>
            </article>

            <article>
              <span>04</span>
              <h3>Temporal Episodes</h3>
              <p>
                Groups nearby change-point detections into higher-level
                episodes.
              </p>
            </article>

            <article>
              <span>05</span>
              <h3>Substantive Evidence</h3>
              <p>
                Connects relationship analysis to resolution and issue-level
                evidence where available.
              </p>
            </article>

            <article>
              <span>06</span>
              <h3>Natural-Language Analysis</h3>
              <p>
                Allows users to interrogate the voting record using analytical
                questions.
              </p>
            </article>
          </div>
        </div>
      </section>

      <section className="about-section">
        <div className="about-label">04 — ARCHITECTURE</div>

        <div className="about-content">
          <h2>A modular analytical architecture.</h2>

          <p>
            The platform separates data, analytical transformations,
            relationship intelligence, API delivery and presentation.
            This allows individual analytical capabilities to evolve without
            requiring the entire system to be redesigned.
          </p>

          <ArchitectureExplorer />

          <div className="arch-future-note">
            <span className="arch-future-label">
              Future Evidence Layer — not currently implemented
            </span>
            <p>
              The architecture leaves clean integration points for evidence
              sources beyond UN voting data. These are potential future
              directions only, not part of the current system:
            </p>
            <ul className="arch-future-list">
              <li>Current Affairs</li>
              <li>Geopolitics</li>
              <li>Speeches</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="about-section">
        <div className="about-label">05 — WHAT IS INNOVATIVE</div>

        <div className="about-content">
          <h2>Not another UN voting dashboard.</h2>

          <p>
            The central idea is to move beyond displaying historical votes
            toward constructing an evidence-backed representation of
            relationships between countries.
          </p>

          <div className="innovation-list">
            <div>
              <strong>01</strong>
              <span>Country-pair relationship intelligence</span>
            </div>

            <div>
              <strong>02</strong>
              <span>Temporal change detection</span>
            </div>

            <div>
              <strong>03</strong>
              <span>Evidence-backed analytical explanations</span>
            </div>

            <div>
              <strong>04</strong>
              <span>Natural-language interrogation of the record</span>
            </div>

            <div>
              <strong>05</strong>
              <span>Provenance-aware analytical outputs</span>
            </div>
          </div>
        </div>
      </section>

      <section className="about-section future-section">
        <div className="about-label">06 — FUTURE DIRECTION</div>

        <div className="about-content">
          <h2>Designed to grow beyond voting records.</h2>

          <p>
            The architecture is deliberately source-agnostic. The current
            analytical foundation is based on UN voting evidence, while the
            underlying design provides clean integration points for additional
            evidence sources in the future.
          </p>

          <div className="future-flow">
            <div>UN VOTING</div>
            <span>+</span>
            <div>RESOLUTION EVIDENCE</div>
            <span>+</span>
            <div>FUTURE EVIDENCE SOURCES</div>
            <span>→</span>
            <div>RICHER RELATIONSHIP INTELLIGENCE</div>
          </div>
        </div>
      </section>

      <footer className="about-footer">
        <div className="about-footer-brand">
          <div className="about-footer-title">UN VOTES INTELLIGENCE</div>
        </div>

        <div className="about-footer-meta">
          <div className="about-footer-row">
            <span className="about-footer-label">Built by</span>
            <span className="about-footer-name">Navya Nawal</span>
          </div>

          <div className="about-footer-row about-footer-role">
            <span className="about-footer-label">Role</span>
            <span>Undergraduate Student</span>
          </div>

          <div className="about-footer-links">
            <a href="mailto:navyanawal4396@gmail.com">
              Email: navyanawal4396@gmail.com
            </a>
            <a
              href="https://github.com/navyanawal0310"
              target="_blank"
              rel="noreferrer noopener"
            >
              GitHub: navyanawal0310
            </a>
            <a
              href="https://www.linkedin.com/in/navya-nawal-97251b362/"
              target="_blank"
              rel="noreferrer noopener"
            >
              LinkedIn: Navya Nawal
            </a>
          </div>
        </div>
      </footer>
    </main>
  );
}