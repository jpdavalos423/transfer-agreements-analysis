import assert from "node:assert/strict";
import test from "node:test";

import { processSetupSubmission } from "../../apps/web/setup_page.js";

test("submitting valid setup data saves payload and navigates to /pathway", () => {
  const calls = [];
  const out = processSetupSubmission(
    {
      college_id: "de_anza",
      target_ucs: ["UCLA", "UCSD"],
      ge_pattern: "IGETC",
      completed_courses: "MATH 1A\n",
    },
    {
      saveRequest: (payload) => calls.push({ type: "save", payload }),
      navigate: (path) => calls.push({ type: "navigate", path }),
    },
  );

  assert.equal(out.ok, true);
  assert.equal(calls.length, 2);
  assert.equal(calls[0].type, "save");
  assert.equal(calls[1].type, "navigate");
  assert.equal(calls[1].path, "/pathway");
  assert.deepEqual(calls[0].payload, {
    college_id: "de_anza",
    target_ucs: ["UCLA", "UCSD"],
    ge_pattern: "IGETC",
    completed_courses: ["MATH 1A"],
  });
});

test("submitting invalid setup data returns validation errors and does not navigate", () => {
  let called = false;
  const out = processSetupSubmission(
    {
      college_id: "",
      target_ucs: [],
      ge_pattern: "",
      completed_courses: "",
    },
    {
      saveRequest: () => {
        called = true;
      },
      navigate: () => {
        called = true;
      },
    },
  );

  assert.equal(out.ok, false);
  assert.equal(called, false);
  assert.deepEqual(
    out.errors.map((e) => e.field).sort(),
    ["college_id", "ge_pattern", "target_ucs"],
  );
});
