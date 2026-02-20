import { GeneratePathwayRequest, GePattern } from "../types";

const ALLOWED_GE_PATTERNS = new Set<GePattern>(["IGETC", "7CoursePattern"]);

export interface SetupFormState {
  college_id: string;
  target_ucs: string[];
  ge_pattern: string;
  completed_courses: string;
}

export interface ValidationIssue {
  field: string;
  message: string;
}

export function parseCompletedCourses(text: string): string[] {
  return String(text || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}

export function dedupeStrings(values: string[]): string[] {
  const out: string[] = [];
  const seen = new Set<string>();
  for (const value of values || []) {
    const normalized = String(value || "").trim();
    if (!normalized || seen.has(normalized)) {
      continue;
    }
    seen.add(normalized);
    out.push(normalized);
  }
  return out;
}

export function buildGeneratePayload(formState: SetupFormState): GeneratePathwayRequest {
  const gePattern = String(formState.ge_pattern || "").trim();
  return {
    college_id: String(formState.college_id || "").trim(),
    target_ucs: dedupeStrings(formState.target_ucs || []),
    ge_pattern: gePattern as GePattern,
    completed_courses: dedupeStrings(parseCompletedCourses(formState.completed_courses || "")),
  };
}

export function validateSetupInput(payload: GeneratePathwayRequest): ValidationIssue[] {
  const errors: ValidationIssue[] = [];

  if (!payload.college_id) {
    errors.push({ field: "college_id", message: "Select a college." });
  }

  if (!Array.isArray(payload.target_ucs) || payload.target_ucs.length === 0) {
    errors.push({ field: "target_ucs", message: "Select at least one UC target." });
  }

  if (!payload.ge_pattern) {
    errors.push({ field: "ge_pattern", message: "Select a GE pattern." });
  } else if (!ALLOWED_GE_PATTERNS.has(payload.ge_pattern)) {
    errors.push({ field: "ge_pattern", message: "GE pattern must be IGETC or 7CoursePattern." });
  }

  return errors;
}
