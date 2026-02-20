export const PlannerUiStates = Object.freeze({
  IDLE: "idle",
  LOADING: "loading",
  SUCCESS: "success",
  ERROR: "error",
});

const ALLOWED_TRANSITIONS = Object.freeze({
  [PlannerUiStates.IDLE]: new Set([PlannerUiStates.LOADING]),
  [PlannerUiStates.LOADING]: new Set([
    PlannerUiStates.SUCCESS,
    PlannerUiStates.ERROR,
    PlannerUiStates.IDLE,
  ]),
  [PlannerUiStates.SUCCESS]: new Set([PlannerUiStates.LOADING]),
  [PlannerUiStates.ERROR]: new Set([PlannerUiStates.LOADING]),
});

export function transitionPlannerState(currentState, nextState) {
  if (currentState === nextState) {
    return currentState;
  }
  const allowed = ALLOWED_TRANSITIONS[currentState];
  if (!allowed || !allowed.has(nextState)) {
    throw new Error(`Invalid planner state transition: ${currentState} -> ${nextState}`);
  }
  return nextState;
}

export function isSubmitAllowed(state) {
  return state !== PlannerUiStates.LOADING;
}
