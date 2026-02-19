import { buildGeneratePayload, validateSetupInput } from "./planner_form.js";

export function processSetupSubmission(formState, deps) {
  const payload = buildGeneratePayload(formState);
  const validationErrors = validateSetupInput(payload);
  if (validationErrors.length > 0) {
    return { ok: false, errors: validationErrors, payload: null };
  }

  deps.saveRequest(payload);
  deps.navigate("/pathway");
  return { ok: true, errors: [], payload };
}
