import assert from "node:assert/strict";
import test from "node:test";

import { createPathwayPageController } from "../../apps/web/pathway_page.js";
import { PATHWAY_REQUEST_STORAGE_KEY } from "../../apps/web/pathway_request_storage.js";

function makeStorage(initialValue = null) {
  const map = new Map();
  if (initialValue != null) {
    map.set(PATHWAY_REQUEST_STORAGE_KEY, JSON.stringify(initialValue));
  }
  return {
    getItem(key) {
      return map.has(key) ? map.get(key) : null;
    },
    setItem(key, value) {
      map.set(key, String(value));
    },
  };
}

test("/pathway initialize with payload triggers one POST and reaches success", async () => {
  let requestCount = 0;
  const payload = {
    college_id: "de_anza",
    target_ucs: ["UCLA"],
    ge_pattern: "IGETC",
    completed_courses: [],
  };
  const controller = createPathwayPageController({
    storage: makeStorage(payload),
    submitGeneratePathway: async (requestPayload) => {
      requestCount += 1;
      assert.deepEqual(requestPayload, payload);
      return { plan: [{ term: "Term 1", courses: [] }], warnings: [] };
    },
  });

  await controller.initialize();
  assert.equal(requestCount, 1);
  const state = controller.getState();
  assert.equal(state.plannerState, "success");
  assert.ok(state.data);
});

test("/pathway success state preserves returned plan ordering", async () => {
  const payload = {
    college_id: "de_anza",
    target_ucs: ["UCLA", "UCSD"],
    ge_pattern: "IGETC",
    completed_courses: [],
  };
  const response = {
    plan: [
      { term: "Term 2", courses: [{ courseCode: "B", units: 3 }] },
      { term: "Term 1", courses: [{ courseCode: "A", units: 3 }] },
    ],
    warnings: [{ severity: "WARN", message: "Gap" }],
  };

  const controller = createPathwayPageController({
    storage: makeStorage(payload),
    submitGeneratePathway: async () => response,
  });

  await controller.initialize();
  const state = controller.getState();
  assert.equal(state.plannerState, "success");
  assert.deepEqual(state.data.plan.map((term) => term.term), ["Term 2", "Term 1"]);
});

test("/pathway error state shows structured error and retry performs one new request", async () => {
  const payload = {
    college_id: "de_anza",
    target_ucs: ["UCLA"],
    ge_pattern: "IGETC",
    completed_courses: [],
  };
  let requestCount = 0;

  const controller = createPathwayPageController({
    storage: makeStorage(payload),
    submitGeneratePathway: async () => {
      requestCount += 1;
      if (requestCount === 1) {
        throw {
          error: {
            code: "VALIDATION_ERROR",
            message: "Request validation failed.",
            details: [{ field: "college_id", message: "invalid" }],
          },
        };
      }
      return { plan: [{ term: "Term 1", courses: [] }], warnings: [] };
    },
  });

  await controller.initialize();
  let state = controller.getState();
  assert.equal(state.plannerState, "error");
  assert.equal(state.error.code, "VALIDATION_ERROR");

  await controller.retry();
  state = controller.getState();
  assert.equal(requestCount, 2);
  assert.equal(state.plannerState, "success");
});

test("/pathway without payload shows idle empty state and no requests", async () => {
  let requestCount = 0;
  const controller = createPathwayPageController({
    storage: makeStorage(null),
    submitGeneratePathway: async () => {
      requestCount += 1;
      return { plan: [], warnings: [] };
    },
  });

  await controller.initialize();
  const state = controller.getState();
  assert.equal(state.plannerState, "idle");
  assert.equal(state.hasPayload, false);
  assert.equal(requestCount, 0);
});

test("/pathway prevents duplicate in-flight retry requests", async () => {
  const payload = {
    college_id: "de_anza",
    target_ucs: ["UCLA"],
    ge_pattern: "IGETC",
    completed_courses: [],
  };
  let resolveRequest;
  let requestCount = 0;

  const controller = createPathwayPageController({
    storage: makeStorage(payload),
    submitGeneratePathway: () => {
      requestCount += 1;
      return new Promise((resolve) => {
        resolveRequest = resolve;
      });
    },
  });

  const first = controller.initialize();
  const second = controller.retry();

  assert.equal(requestCount, 1);
  resolveRequest({ plan: [{ term: "Term 1", courses: [] }], warnings: [] });
  await first;
  await second;

  const state = controller.getState();
  assert.equal(state.plannerState, "success");
  assert.equal(requestCount, 1);
});

test("/pathway prevents duplicate in-flight initialize requests", async () => {
  const payload = {
    college_id: "de_anza",
    target_ucs: ["UCLA"],
    ge_pattern: "IGETC",
    completed_courses: [],
  };
  let resolveRequest;
  let requestCount = 0;

  const controller = createPathwayPageController({
    storage: makeStorage(payload),
    submitGeneratePathway: () => {
      requestCount += 1;
      return new Promise((resolve) => {
        resolveRequest = resolve;
      });
    },
  });

  const first = controller.initialize();
  const second = controller.initialize();

  assert.equal(requestCount, 1);
  resolveRequest({ plan: [{ term: "Term 1", courses: [] }], warnings: [] });
  await first;
  await second;

  const state = controller.getState();
  assert.equal(state.plannerState, "success");
  assert.equal(requestCount, 1);
});

test("/pathway exposes loading state while request is in flight", async () => {
  const payload = {
    college_id: "de_anza",
    target_ucs: ["UCLA"],
    ge_pattern: "IGETC",
    completed_courses: [],
  };
  let resolveRequest;
  const controller = createPathwayPageController({
    storage: makeStorage(payload),
    submitGeneratePathway: () =>
      new Promise((resolve) => {
        resolveRequest = resolve;
      }),
  });

  const pending = controller.initialize();
  const loadingState = controller.getState();
  assert.equal(loadingState.plannerState, "loading");
  assert.equal(loadingState.isLoading, true);

  resolveRequest({ plan: [{ term: "Term 1", courses: [] }], warnings: [] });
  await pending;
  assert.equal(controller.getState().plannerState, "success");
});
