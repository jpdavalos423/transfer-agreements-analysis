export const PATHWAY_REQUEST_STORAGE_KEY = "tpp.pathway.request.v1";

function resolveStorage(storage) {
  if (storage) {
    return storage;
  }
  return globalThis?.window?.sessionStorage ?? null;
}

export function savePathwayRequest(payload, storage) {
  const target = resolveStorage(storage);
  if (!target) {
    throw new Error("Session storage is unavailable.");
  }
  target.setItem(PATHWAY_REQUEST_STORAGE_KEY, JSON.stringify(payload));
}

export function loadPathwayRequest(storage) {
  const target = resolveStorage(storage);
  if (!target) {
    return null;
  }
  const raw = target.getItem(PATHWAY_REQUEST_STORAGE_KEY);
  if (!raw) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}
