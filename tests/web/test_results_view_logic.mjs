import assert from "node:assert/strict";
import test from "node:test";

import { buildResultsViewModel, formatUnits } from "../../apps/web/results_view.js";

test("buildResultsViewModel preserves API term and course ordering", () => {
  const response = {
    plan: [
      {
        term: "Term 2",
        courses: [
          { courseCode: "B COURSE", units: 4 },
          { courseCode: "A COURSE", units: 3 },
        ],
      },
      {
        term: "Term 1",
        courses: [{ courseCode: "C COURSE", units: 2 }],
      },
    ],
  };

  const model = buildResultsViewModel(response);
  assert.equal(model.isEmpty, false);
  assert.equal(model.terms[0].term, "Term 2");
  assert.equal(model.terms[1].term, "Term 1");
  assert.equal(model.terms[0].courses[0].courseCode, "B COURSE");
  assert.equal(model.terms[0].courses[1].courseCode, "A COURSE");
});

test("buildResultsViewModel computes term totals and overall total", () => {
  const response = {
    plan: [
      {
        term: "Term 1",
        courses: [
          { courseCode: "MATH 1A", units: 5 },
          { courseCode: "CIS 22A", units: 4.5 },
        ],
      },
      {
        term: "Term 2",
        courses: [{ courseCode: "IG_1A", units: 3 }],
      },
    ],
  };

  const model = buildResultsViewModel(response);
  assert.equal(model.terms[0].termUnits, 9.5);
  assert.equal(model.terms[1].termUnits, 3);
  assert.equal(model.overallUnits, 12.5);
  assert.equal(formatUnits(model.overallUnits), "12.5");
});

test("buildResultsViewModel returns empty state for empty plan", () => {
  const model = buildResultsViewModel({ plan: [] });
  assert.equal(model.isEmpty, true);
  assert.equal(model.terms.length, 0);
  assert.equal(model.overallUnits, 0);
  assert.match(model.emptyMessage, /No pathway terms were returned/i);
});

