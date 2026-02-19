import assert from "node:assert/strict";
import test from "node:test";

import {
  PlannerUiStates,
  isSubmitAllowed,
  transitionPlannerState,
} from "../../apps/web/planner_state.js";

test("transitionPlannerState allows idle -> loading -> success", () => {
  const loading = transitionPlannerState(PlannerUiStates.IDLE, PlannerUiStates.LOADING);
  const success = transitionPlannerState(loading, PlannerUiStates.SUCCESS);
  assert.equal(loading, PlannerUiStates.LOADING);
  assert.equal(success, PlannerUiStates.SUCCESS);
});

test("transitionPlannerState allows idle -> loading -> error", () => {
  const loading = transitionPlannerState(PlannerUiStates.IDLE, PlannerUiStates.LOADING);
  const error = transitionPlannerState(loading, PlannerUiStates.ERROR);
  assert.equal(error, PlannerUiStates.ERROR);
});

test("transitionPlannerState allows loading -> idle for reset/back recovery", () => {
  const idle = transitionPlannerState(PlannerUiStates.LOADING, PlannerUiStates.IDLE);
  assert.equal(idle, PlannerUiStates.IDLE);
});

test("transitionPlannerState allows retry from success and error", () => {
  const loadingFromSuccess = transitionPlannerState(
    PlannerUiStates.SUCCESS,
    PlannerUiStates.LOADING,
  );
  const loadingFromError = transitionPlannerState(
    PlannerUiStates.ERROR,
    PlannerUiStates.LOADING,
  );
  assert.equal(loadingFromSuccess, PlannerUiStates.LOADING);
  assert.equal(loadingFromError, PlannerUiStates.LOADING);
});

test("transitionPlannerState throws on invalid transition", () => {
  assert.throws(
    () => transitionPlannerState(PlannerUiStates.IDLE, PlannerUiStates.SUCCESS),
    /Invalid planner state transition: idle -> success/,
  );
});

test("isSubmitAllowed returns false only while loading", () => {
  assert.equal(isSubmitAllowed(PlannerUiStates.IDLE), true);
  assert.equal(isSubmitAllowed(PlannerUiStates.SUCCESS), true);
  assert.equal(isSubmitAllowed(PlannerUiStates.ERROR), true);
  assert.equal(isSubmitAllowed(PlannerUiStates.LOADING), false);
});
