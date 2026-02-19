const ALLOWED_GE_PATTERNS = new Set(["IGETC", "7CoursePattern"]);

export function parseCompletedCourses(text) {
  return String(text || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}

export function dedupeStrings(values) {
  const out = [];
  const seen = new Set();
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

export function buildGeneratePayload(formState) {
  return {
    college_id: String(formState?.college_id || "").trim(),
    target_ucs: dedupeStrings(formState?.target_ucs || []),
    ge_pattern: String(formState?.ge_pattern || "").trim(),
    completed_courses: dedupeStrings(
      parseCompletedCourses(formState?.completed_courses || ""),
    ),
  };
}

export function validateSetupInput(payload) {
  const errors = [];
  if (!payload || typeof payload !== "object") {
    return [{ field: "form", message: "Invalid form data." }];
  }
  if (!payload.college_id) {
    errors.push({ field: "college_id", message: "Select a college." });
  }
  if (!Array.isArray(payload.target_ucs) || payload.target_ucs.length === 0) {
    errors.push({
      field: "target_ucs",
      message: "Select at least one UC target.",
    });
  }
  if (!payload.ge_pattern) {
    errors.push({ field: "ge_pattern", message: "Select a GE pattern." });
  } else if (!ALLOWED_GE_PATTERNS.has(payload.ge_pattern)) {
    errors.push({
      field: "ge_pattern",
      message: "GE pattern must be IGETC or 7CoursePattern.",
    });
  }
  return errors;
}

export function extractApiError(payload) {
  const code = payload?.error?.code || "REQUEST_FAILED";
  const message =
    payload?.error?.message || "Unable to complete request. Please try again.";
  const details = Array.isArray(payload?.error?.details)
    ? payload.error.details
        .filter(
          (d) =>
            d &&
            typeof d === "object" &&
            typeof d.field === "string" &&
            typeof d.message === "string"
        )
        .map((d) => ({ field: d.field, message: d.message }))
    : [];
  return { code, message, details };
}
