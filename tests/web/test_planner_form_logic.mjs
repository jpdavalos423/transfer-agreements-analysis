import assert from "node:assert/strict";
import test from "node:test";

import {
  buildGeneratePayload,
  extractApiError,
  parseCompletedCourses,
  validateSetupInput,
} from "../../apps/web/planner_form.js";

test("parseCompletedCourses splits one-per-line and trims", () => {
  const courses = parseCompletedCourses(" MATH 1A \n\nCIS 22A\n  ");
  assert.deepEqual(courses, ["MATH 1A", "CIS 22A"]);
});

test("buildGeneratePayload returns shared_types-compatible request shape", () => {
  const payload = buildGeneratePayload({
    college_id: " de_anza ",
    target_ucs: ["UCLA", "UCSD", "UCLA"],
    ge_pattern: "IGETC",
    completed_courses: "MATH 1A\nCIS 22A\n",
  });

  assert.deepEqual(Object.keys(payload).sort(), [
    "college_id",
    "completed_courses",
    "ge_pattern",
    "target_ucs",
  ]);
  assert.equal(payload.college_id, "de_anza");
  assert.deepEqual(payload.target_ucs, ["UCLA", "UCSD"]);
  assert.equal(payload.ge_pattern, "IGETC");
  assert.deepEqual(payload.completed_courses, ["MATH 1A", "CIS 22A"]);
});

test("validateSetupInput enforces required fields", () => {
  const errors = validateSetupInput({
    college_id: "",
    target_ucs: [],
    ge_pattern: "",
    completed_courses: [],
  });

  const fields = errors.map((e) => e.field).sort();
  assert.deepEqual(fields, ["college_id", "ge_pattern", "target_ucs"]);
});

test("validateSetupInput accepts valid input", () => {
  const errors = validateSetupInput({
    college_id: "de_anza",
    target_ucs: ["UCLA"],
    ge_pattern: "7CoursePattern",
    completed_courses: [],
  });
  assert.deepEqual(errors, []);
});

test("extractApiError reads structured error envelope", () => {
  const parsed = extractApiError({
    error: {
      code: "VALIDATION_ERROR",
      message: "Request validation failed.",
      details: [{ field: "college_id", message: "Select a college." }],
    },
  });

  assert.equal(parsed.code, "VALIDATION_ERROR");
  assert.equal(parsed.message, "Request validation failed.");
  assert.deepEqual(parsed.details, [
    { field: "college_id", message: "Select a college." },
  ]);
});

