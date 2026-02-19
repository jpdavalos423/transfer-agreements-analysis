const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export function getApiBaseUrl() {
  const injected = globalThis?.window?.__TPP_API_BASE_URL;
  if (typeof injected === "string" && injected.trim() !== "") {
    return injected.trim();
  }
  return DEFAULT_API_BASE_URL;
}

function buildUrl(path) {
  return `${getApiBaseUrl()}${path}`;
}

async function requestJson(path, options = {}) {
  const response = await fetch(buildUrl(path), options);
  const payload = await response.json();
  if (!response.ok) {
    throw payload;
  }
  return payload;
}

export async function fetchColleges() {
  return requestJson("/v1/metadata/colleges", { method: "GET" });
}

export async function fetchUcs() {
  return requestJson("/v1/metadata/ucs", { method: "GET" });
}

export async function submitGeneratePathway(payload) {
  return requestJson("/v1/pathways/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

