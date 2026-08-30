// The frontend dev server (Vite) and the FastAPI backend (uvicorn) run on
// different origins/ports. A relative "/api/v1" path resolves against
// whichever server served the page — in dev that's Vite, which has no route
// for /api/v1/* and falls back to index.html, handing us HTML instead of
// JSON. Point this at the real backend, overridable via env var so it still
// works in any deployment (proxied prod, docker-compose, etc).
const DEFAULT_API_ORIGIN = "http://localhost:8000";

const API_ORIGIN =
  (typeof import.meta !== "undefined" &&
    import.meta.env &&
    import.meta.env.VITE_API_BASE_URL) ||
  DEFAULT_API_ORIGIN;

const BASE_URL = `${API_ORIGIN.replace(/\/$/, "")}/api/v1`;

async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  let response;

  try {
    response = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch (networkError) {
    throw new Error(
      `Could not reach the API at ${url}. Is the FastAPI backend running ` +
        `on ${API_ORIGIN}? (${networkError.message})`
    );
  }

  const contentType = response.headers.get("content-type") || "";

  if (!contentType.includes("application/json")) {
    const preview = (await response.text()).slice(0, 120);

    throw new Error(
      `Expected JSON from ${url} but got "${contentType || "unknown"}" ` +
        `instead. This usually means the request never reached the FastAPI ` +
        `backend — check VITE_API_BASE_URL and that the backend is running. ` +
        `Response started with: ${preview}`
    );
  }

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;

    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // response had no JSON body — fall back to the generic message
    }

    throw new Error(detail);
  }

  return response.json();
}

export function getCountries() {
  return request("/countries");
}

export function getRelationship(countryA, countryB) {
  return request(
    `/relationship/${encodeURIComponent(countryA)}/${encodeURIComponent(
      countryB
    )}`
  );
}

export function getRelationshipHistory(countryA, countryB) {
  return request(
    `/relationship/${encodeURIComponent(countryA)}/${encodeURIComponent(
      countryB
    )}/history`
  );
}

export function getRelationshipChanges(countryA, countryB) {
  return request(
    `/relationship/${encodeURIComponent(countryA)}/${encodeURIComponent(
      countryB
    )}/changes`
  );
}

export function runIntelligenceQuery(question, countryA, countryB) {
  return request("/query", {
    method: "POST",
    body: JSON.stringify({
      question,
      country_a: countryA,
      country_b: countryB,
    }),
  });
}