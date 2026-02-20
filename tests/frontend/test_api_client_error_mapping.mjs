import test from "node:test";
import assert from "node:assert/strict";

import { mapApiErrorToUiStateRuntime } from "../../apps/frontend/src/api/error_mapping.js";

test("maps structured api error to ui error state", () => {
  const mapped = mapApiErrorToUiStateRuntime({
    code: "VALIDATION_ERROR",
    message: "Request validation failed.",
    details: [
      { field: "college_id", message: "Invalid college" },
      { field: 123, message: "bad" },
    ],
  });

  assert.deepEqual(mapped, {
    code: "VALIDATION_ERROR",
    message: "Request validation failed.",
    details: [{ field: "college_id", message: "Invalid college" }],
  });
});

test("maps unknown error to fallback ui error state", () => {
  const mapped = mapApiErrorToUiStateRuntime(new Error("boom"));

  assert.deepEqual(mapped, {
    code: "REQUEST_FAILED",
    message: "Unable to complete request. Please try again.",
    details: [],
  });
});
