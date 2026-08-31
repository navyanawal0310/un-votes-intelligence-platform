import { useEffect, useMemo, useState } from "react";
import isoCountries from "i18n-iso-countries";
import en from "i18n-iso-countries/langs/en.json";
import WorldMap from "./components/map/WorldMap";
import "./styles/dashboard.css";
import {
  getCountries,
  getRelationship,
  getRelationshipHistory,
  getRelationshipChanges,
  runIntelligenceQuery,
} from "./api/client";
import RelationshipProfile from "./components/relationship/RelationshipProfile";

isoCountries.registerLocale(en);

function countryName(code) {
  if (!code) return "Select a country";

  try {
    return (
      isoCountries.getName(code, "en", { select: "official" }) ||
      isoCountries.getName(code, "en") ||
      code
    );
  } catch {
    return code;
  }
}

function App() {
  const [countryA, setCountryA] = useState("IND");
  const [countryB, setCountryB] = useState("CHN");
  const [selectionMode, setSelectionMode] = useState("B");

  const [relationship, setRelationship] = useState(null);
  const [history, setHistory] = useState(null);
  const [changes, setChanges] = useState([]);
  const [query, setQuery] = useState("");
  const [queryResult, setQueryResult] = useState(null);
  const [queryLoading, setQueryLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [availableCountries, setAvailableCountries] = useState([]);
  const [countriesLoading, setCountriesLoading] = useState(true);

  const selectedA = useMemo(
    () => ({ code: countryA, name: countryName(countryA) }),
    [countryA]
  );

  const selectedB = useMemo(
    () => ({ code: countryB, name: countryName(countryB) }),
    [countryB]
  );

  async function loadRelationship(a = countryA, b = countryB) {
    if (!a || !b) {
      setError("Select two countries to compare.");
      return;
    }

    if (a === b) {
      setError("Choose two different countries.");
      return;
    }

    setLoading(true);
    setError("");
    setQueryResult(null);

    try {
      const response = await getRelationship(a, b);
      setRelationship(response);

      try {
        const [historyResponse, changesResponse] = await Promise.all([
          getRelationshipHistory(a, b),
          getRelationshipChanges(a, b),
        ]);

        setHistory(historyResponse);
        setChanges(changesResponse.changes || []);
      } catch (detailError) {
        console.warn(
          "Additional relationship evidence unavailable:",
          detailError
        );
        setHistory(null);
        setChanges([]);
      }
    } catch (err) {
      setRelationship(null);
      setHistory(null);
      setChanges([]);
      setError(err.message || "The analytical profile could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  function selectCountry(selection) {
    if (selection?.action === "clear") {
      if (selection.country === countryA) setCountryA(null);
      if (selection.country === countryB) setCountryB(null);

      setRelationship(null);
      setError("");
      return;
    }

    const code = selection;
    if (!code) return;

    if (selectionMode === "A") {
      if (code === countryB) {
        setError("That country is already Country B.");
        return;
      }

      setCountryA(code);
      setRelationship(null);
      setError("");
      return;
    }

    if (selectionMode === "B") {
      if (code === countryA) {
        setError("That country is already Country A.");
        return;
      }

      setCountryB(code);
      setRelationship(null);
      setError("");
    }
  }

  function swapCountries() {
    setCountryA(countryB);
    setCountryB(countryA);
    setError("");
  }

  useEffect(() => {
    async function loadCountries() {
      try {
        const data = await getCountries();
        setAvailableCountries(data.countries || []);
      } catch {
        setError("Unable to load the country universe.");
      } finally {
        setCountriesLoading(false);
      }
    }

    loadCountries();
  }, []);

  useEffect(() => {
    loadRelationship();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="site-shell">
      <header className="site-header">
        <div className="wordmark">
          <span className="wordmark-main">UN Votes</span>
          <span className="wordmark-secondary">Intelligence</span>
        </div>

        <nav>
          <a href="#explore">Explore</a>
          <a href="#methodology">Methodology</a>
        </nav>
      </header>

      <main>
        <section className="hero" id="explore">
          <div className="hero-copy">
            <p className="section-label">
              UNITED NATIONS · VOTING INTELLIGENCE
            </p>

            <h1>
              UN Voting
              <br />
              <em>Intelligence Platform</em>
            </h1>

            <p className="hero-description">
              Explore diplomatic alignment through decades of United Nations
              voting behaviour.
            </p>
          </div>

          <div className="hero-note">
            <span>Case file</span>
            Select a country on the map, then a second to compare. The
            record builds itself below.
          </div>
        </section>

        <section className="atlas-section">
          <div className="atlas-header">
            <div>
              <p className="section-label">GLOBAL ATLAS</p>
              <h2>Voting relationships</h2>
            </div>

            <div className="atlas-selection">
              <button
                type="button"
                className={
                  selectionMode === "A"
                    ? "country-selector active"
                    : "country-selector"
                }
                onClick={() => setSelectionMode("A")}
              >
                <span className="selection-dot selected" />
                {selectedA.name}
              </button>

              <button
                type="button"
                className="selection-divider"
                onClick={swapCountries}
                title="Swap countries"
              >
                ⇄
              </button>

              <button
                type="button"
                className={
                  selectionMode === "B"
                    ? "country-selector active"
                    : "country-selector"
                }
                onClick={() => setSelectionMode("B")}
              >
                <span className="selection-dot comparison" />
                {selectedB.name}
              </button>
            </div>
          </div>

          <div className="atlas">
            <WorldMap
              selectedCountry={countryA}
              comparisonCountry={countryB}
              availableCountries={availableCountries}
              onCountrySelect={selectCountry}
            />

            <div className="map-caption">
              <span>1946—2025</span>
              <span>
                {countriesLoading
                  ? "Loading country universe…"
                  : `${availableCountries.length} countries on record`}
              </span>
            </div>
          </div>

          <div className="comparison-action">
            <button
              onClick={() => loadRelationship(countryA, countryB)}
              disabled={loading || !countryA || !countryB || countryA === countryB}
            >
              {loading ? "Building the file…" : "Open the file"}
            </button>
          </div>
        </section>

        {error && (
          <section className="notice">
            <strong>Unable to load profile</strong>
            <span>{error}</span>
          </section>
        )}

        {loading && (
          <section className="relationship-loading">
            <div className="loading-line large" />
            <div className="loading-line medium" />
            <div className="loading-line small" />
          </section>
        )}

        {relationship && !loading && (
          <section className="dossier-section-wrap">
            <RelationshipProfile
              relationship={relationship}
              history={history}
              changes={changes}
              countryA={countryA}
              countryB={countryB}
              query={query}
              setQuery={setQuery}
              queryResult={queryResult}
              queryLoading={queryLoading}
              onAsk={async () => {
                setQueryLoading(true);
                try {
                  const result = await runIntelligenceQuery(
                    query,
                    countryA || relationship.country_a,
                    countryB || relationship.country_b
                  );
                  setQueryResult(result);
                } catch (err) {
                  setQueryResult({ answer: err.message });
                } finally {
                  setQueryLoading(false);
                }
              }}
            />
          </section>
        )}

        <section className="methodology" id="methodology">
          <div>
            <p className="section-label">HOW TO READ THIS</p>

            <h2>
              Voting alignment is evidence,
              <br />
              not a verdict.
            </h2>
          </div>

          <div className="methodology-copy">
            <p>
              The analyzer compares observed voting behaviour in the United
              Nations General Assembly. The resulting relationship score
              describes the statistical degree of alignment in the available
              voting record.
            </p>

            <p>
              Explore the evidence before drawing conclusions about
              diplomatic relationships.
            </p>
          </div>
        </section>
      </main>

      <footer>
        <span>UN Votes Intelligence</span>
        <span>Analytical evidence · UN voting record</span>
      </footer>
    </div>
  );
}

export default App;