import { submitGeneratePathway } from "./api_client.js";
import { extractApiError } from "./planner_form.js";
import {
  PlannerUiStates,
  isSubmitAllowed,
  transitionPlannerState,
} from "./planner_state.js";
import { loadPathwayRequest } from "./pathway_request_storage.js";

export function createPathwayPageController(deps = {}) {
  const submit = deps.submitGeneratePathway || submitGeneratePathway;
  const storage = deps.storage;
  const onStateChange = deps.onStateChange || (() => {});

  let plannerState = PlannerUiStates.IDLE;
  let payload = null;
  let data = null;
  let error = null;

  function snapshot() {
    return {
      plannerState,
      payload,
      data,
      error,
      hasPayload: payload !== null,
      canRetry:
        payload !== null &&
        (plannerState === PlannerUiStates.ERROR || plannerState === PlannerUiStates.IDLE),
      isLoading: plannerState === PlannerUiStates.LOADING,
    };
  }

  function emit() {
    onStateChange(snapshot());
  }

  function setState(nextState) {
    plannerState = transitionPlannerState(plannerState, nextState);
    emit();
  }

  async function runRequest() {
    if (payload === null || !isSubmitAllowed(plannerState)) {
      return;
    }

    setState(PlannerUiStates.LOADING);
    error = null;
    data = null;
    emit();

    try {
      data = await submit(payload);
      setState(PlannerUiStates.SUCCESS);
    } catch (err) {
      error = extractApiError(err);
      setState(PlannerUiStates.ERROR);
    }
  }

  async function initialize() {
    payload = loadPathwayRequest(storage);
    error = null;
    data = null;
    emit();

    if (payload === null) {
      return;
    }

    await runRequest();
  }

  async function retry() {
    await runRequest();
  }

  return {
    initialize,
    retry,
    getState: snapshot,
  };
}
