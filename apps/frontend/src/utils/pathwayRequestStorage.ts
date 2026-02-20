import { GeneratePathwayRequest } from "../types";

export const PATHWAY_REQUEST_STORAGE_KEY = "tpp.pathway.request.v1";

function resolveStorage(storage?: Storage | null): Storage | null {
  if (storage) {
    return storage;
  }
  return globalThis?.window?.sessionStorage ?? null;
}

export function savePathwayRequest(payload: GeneratePathwayRequest, storage?: Storage | null): void {
  const target = resolveStorage(storage);
  if (!target) {
    throw new Error("Session storage is unavailable.");
  }
  target.setItem(PATHWAY_REQUEST_STORAGE_KEY, JSON.stringify(payload));
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

export function loadPathwayRequest(storage?: Storage | null): GeneratePathwayRequest | null {
  const target = resolveStorage(storage);
  if (!target) {
    return null;
  }

  const raw = target.getItem(PATHWAY_REQUEST_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as Partial<GeneratePathwayRequest>;
    if (!parsed || typeof parsed !== "object") {
      return null;
    }
    if (
      typeof parsed.college_id !== "string" ||
      !isStringArray(parsed.target_ucs) ||
      typeof parsed.ge_pattern !== "string" ||
      !isStringArray(parsed.completed_courses)
    ) {
      return null;
    }

    return {
      college_id: parsed.college_id,
      target_ucs: parsed.target_ucs,
      ge_pattern: parsed.ge_pattern,
      completed_courses: parsed.completed_courses,
    };
  } catch {
    return null;
  }
}
