import assert from "node:assert/strict";
import test from "node:test";

import {
  buildStatusViewModel,
  deriveConfidenceLabel,
} from "../../apps/web/status_panel.js";

test("confidence is complete with no warnings when plan exists and warnings are empty", () => {
  const payload = {
    plan: [{ term: "Term 1", courses: [{ courseCode: "MATH 1A", units: 5 }] }],
    warnings: [],
  };
  assert.equal(deriveConfidenceLabel(payload), "Complete with no warnings");
});

test("confidence is complete with caveats when plan exists and warnings are present", () => {
  const payload = {
    plan: [{ term: "Term 1", courses: [{ courseCode: "MATH 1A", units: 5 }] }],
    warnings: [{ severity: "WARN", message: "Articulation gap." }],
  };
  assert.equal(deriveConfidenceLabel(payload), "Complete with caveats");
});

test("confidence is incomplete when plan is empty", () => {
  const payload = { plan: [], warnings: [{ severity: "WARN", message: "x" }] };
  assert.equal(deriveConfidenceLabel(payload), "Incomplete");
});

test("confidence is incomplete when backend explicitly marks incomplete", () => {
  const payload = {
    plan: [{ term: "Term 1", courses: [{ courseCode: "MATH 1A", units: 5 }] }],
    warnings: [],
    completion_status: "incomplete",
  };
  assert.equal(deriveConfidenceLabel(payload), "Incomplete");
});

test("view model omits unmet requirements section when not provided", () => {
  const model = buildStatusViewModel({
    plan: [{ term: "Term 1", courses: [{ courseCode: "MATH 1A", units: 5 }] }],
    warnings: [],
  });
  assert.equal(model.hasUnmetRequirements, false);
  assert.deepEqual(model.unmetRequirements, []);
});
