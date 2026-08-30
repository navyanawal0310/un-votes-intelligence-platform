import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
} from "@vnedyalk0v/react19-simple-maps";
import "./WorldMap.css";
import { geoCentroid } from "d3-geo";
import countries from "i18n-iso-countries";
import world from "world-atlas/countries-110m.json";
import en from "i18n-iso-countries/langs/en.json";


countries.registerLocale(en);

function numericToAlpha3(id) {
  if (!id) return null;

  const numeric = String(id).padStart(3, "0");

  try {
    return countries.numericToAlpha3(numeric);
  } catch {
    return null;
  }
}

function getCountryName(code) {
  if (!code) return "Unknown country";

  try {
    return (
      countries.getName(code, "en", { select: "official" }) ||
      countries.getName(code, "en") ||
      code
    );
  } catch {
    return code;
  }
}

function normaliseAvailableCountries(list) {
  return new Set(
    (list || [])
      .map((item) => {
        if (typeof item === "string") {
          return item.toUpperCase();
        }

        return (
          item?.code ||
          item?.country_code ||
          item?.iso3 ||
          item?.alpha3 ||
          ""
        ).toUpperCase();
      })
      .filter(Boolean)
  );
}

function WorldMap({
  selectedCountry,
  comparisonCountry,
  availableCountries = [],
  onCountrySelect,
}) {
  const analyticalCountries =
    normaliseAvailableCountries(availableCountries);

  return (
    <div className="world-map">
      <ComposableMap
        projection="geoEqualEarth"
        projectionConfig={{
          scale: 145,
          center: [10, 5],
        }}
        width={1000}
        height={520}
      >
        <Geographies geography={world}>
          {({ geographies }) => (
            <>
              {geographies.map((geo) => {
                const code = numericToAlpha3(geo.id);

                if (!code) return null;

                const isSelected = code === selectedCountry;
                const isComparison = code === comparisonCountry;

                /*
                 * Selected countries must remain visible even if the
                 * API country list is temporarily loading.
                 */
                const isAnalytical =
                  analyticalCountries.size === 0 ||
                  analyticalCountries.has(code) ||
                  isSelected ||
                  isComparison;

                return (
                  <Geography
                    key={geo.rsmKey}
                    geography={geo}
                    onClick={() => {
                      if (!isAnalytical) return;
                      onCountrySelect(code);
                    }}
                    onDoubleClick={(event) => {
                      event.preventDefault();
                      if (!isAnalytical) return;

                      if (code === selectedCountry) {
                        onCountrySelect({
                          action: "clear",
                          country: code,
                        });
                        return;
                      }

                      if (code === comparisonCountry) {
                        onCountrySelect({
                          action: "clear",
                          country: code,
                        });
                      }
                    }}
                    title={
                      isAnalytical
                        ? getCountryName(code)
                        : `${getCountryName(code)} — analytical data unavailable`
                    }
                    style={{
                      default: {
                        fill: isSelected
                          ? "#1f5c52"
                          : isComparison
                          ? "#8c2f2b"
                          : isAnalytical
                          ? "#cabb90"
                          : "#e2d6ac",

                        stroke: "#e9ddc0",
                        strokeWidth: 0.55,
                        outline: "none",
                        opacity: isAnalytical ? 1 : 0.55,
                      },

                      hover: {
                        fill: isSelected
                          ? "#1f5c52"
                          : isComparison
                          ? "#8c2f2b"
                          : isAnalytical
                          ? "#a9762f"
                          : "#e2d6ac",

                        stroke: isAnalytical
                          ? "#221a10"
                          : "#e9ddc0",

                        strokeWidth: isAnalytical ? 0.8 : 0.55,
                        outline: "none",
                        cursor: isAnalytical
                          ? "pointer"
                          : "default",
                      },

                      pressed: {
                        fill: isSelected
                          ? "#1f5c52"
                          : isComparison
                          ? "#8c2f2b"
                          : "#a9762f",
                        outline: "none",
                      },
                    }}
                  />
                );
              })}

              {geographies.map((geo) => {
                const code = numericToAlpha3(geo.id);

                if (
                  code !== selectedCountry &&
                  code !== comparisonCountry
                ) {
                  return null;
                }

                if (!code) return null;

                let coordinates;

                try {
                  coordinates = geoCentroid(geo);
                } catch {
                  return null;
                }

                if (
                  !coordinates ||
                  !Number.isFinite(coordinates[0]) ||
                  !Number.isFinite(coordinates[1])
                ) {
                  return null;
                }

                const isSelected = code === selectedCountry;

                return (
                  <Marker
                    key={`marker-${geo.rsmKey}`}
                    coordinates={coordinates}
                  >
                    <circle
                      r={6}
                      fill={isSelected ? "#1f5c52" : "#8c2f2b"}
                      stroke="#e9ddc0"
                      strokeWidth={2}
                    />

                    <text
                      textAnchor="middle"
                      y={-12}
                      style={{
                        fontFamily: "'IBM Plex Mono', monospace",
                        fontSize: "11px",
                        fontWeight: 600,
                        fill: "#221a10",
                        pointerEvents: "none",
                      }}
                    >
                      {code}
                    </text>
                  </Marker>
                );
              })}
            </>
          )}
        </Geographies>
      </ComposableMap>
      <div className="map-instruction">
      <span className="map-instruction-icon">i</span>
      <div className="map-instruction-text">
        <strong>Explore the map</strong>
        <span>Click to select a country.</span>
        <span>Select a second country to compare.</span>
        <span>Double-click a selected country to remove it.</span>
      </div>
    </div>
    </div>
  );
}

export default WorldMap;