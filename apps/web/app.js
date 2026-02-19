import { fetchColleges, fetchUcs } from "./api_client.js";
import {
  PlannerUiStates,
  isSubmitAllowed,
  transitionPlannerState,
} from "./planner_state.js";
import { savePathwayRequest } from "./pathway_request_storage.js";
import { processSetupSubmission } from "./setup_page.js";

const form = document.getElementById("planner-form");
const collegeSelect = document.getElementById("college_id");
const ucSelect = document.getElementById("target_ucs");
const geSelect = document.getElementById("ge_pattern");
const completedCoursesInput = document.getElementById("completed_courses");
const submitButton = document.getElementById("submit-button");

const setupErrorsPanel = document.getElementById("setup-errors-panel");
const setupErrorsList = document.getElementById("setup-errors-list");
const apiErrorPanel = document.getElementById("api-error-panel");
const apiErrorHeadline = document.getElementById("api-error-headline");
const apiErrorDetails = document.getElementById("api-error-details");

let plannerState = PlannerUiStates.IDLE;

function clearElementChildren(el) {
  if (!el) {
    return;
  }
  el.innerHTML = "";
}

function createOption(value, label, selected = false) {
  const option = document.createElement("option");
  option.value = value;
  option.textContent = label;
  option.selected = selected;
  return option;
}

function setSelectLoading(selectEl, loadingLabel) {
  selectEl.disabled = true;
  clearElementChildren(selectEl);
  selectEl.appendChild(createOption("", loadingLabel, true));
}

function setSelectError(selectEl, message) {
  selectEl.disabled = true;
  clearElementChildren(selectEl);
  selectEl.appendChild(createOption("", message, true));
}

function renderSetupErrors(errors) {
  clearElementChildren(setupErrorsList);
  if (!errors || errors.length === 0) {
    setupErrorsPanel.hidden = true;
    return;
  }
  setupErrorsPanel.hidden = false;
  for (const error of errors) {
    const li = document.createElement("li");
    li.textContent = error.message;
    setupErrorsList.appendChild(li);
  }
}

function renderApiError(message, details = []) {
  apiErrorHeadline.textContent = message;
  clearElementChildren(apiErrorDetails);
  for (const detail of details) {
    const li = document.createElement("li");
    li.textContent = detail;
    apiErrorDetails.appendChild(li);
  }
  apiErrorPanel.hidden = false;
}

function hideApiError() {
  apiErrorPanel.hidden = true;
  apiErrorHeadline.textContent = "";
  clearElementChildren(apiErrorDetails);
}

function populateCollegeOptions(items) {
  clearElementChildren(collegeSelect);
  collegeSelect.appendChild(createOption("", "Select a college...", true));
  for (const item of items) {
    collegeSelect.appendChild(createOption(item.id, item.name, false));
  }
  collegeSelect.disabled = false;
}

function populateUcOptions(items) {
  clearElementChildren(ucSelect);
  for (const item of items) {
    ucSelect.appendChild(createOption(item.id, item.name, false));
  }
  ucSelect.disabled = false;
}

function getSelectedUcValues() {
  return Array.from(ucSelect.selectedOptions).map((opt) => opt.value);
}

async function loadMetadata() {
  setSelectLoading(collegeSelect, "Loading colleges...");
  setSelectLoading(ucSelect, "Loading UCs...");

  try {
    const [collegesPayload, ucsPayload] = await Promise.all([
      fetchColleges(),
      fetchUcs(),
    ]);
    const colleges = Array.isArray(collegesPayload?.data)
      ? collegesPayload.data
      : [];
    const ucs = Array.isArray(ucsPayload?.data) ? ucsPayload.data : [];

    populateCollegeOptions(colleges);
    populateUcOptions(ucs);
  } catch {
    setSelectError(collegeSelect, "Unable to load colleges.");
    setSelectError(ucSelect, "Unable to load UC options.");
    renderApiError("Failed to load setup options.");
  }
}

function setSubmittingState(isSubmitting) {
  submitButton.disabled = isSubmitting;
  submitButton.textContent = isSubmitting
    ? "Continuing..."
    : "Generate Pathway";
}

function setPlannerState(nextState) {
  plannerState = transitionPlannerState(plannerState, nextState);
  setSubmittingState(plannerState === PlannerUiStates.LOADING);
}

function readCurrentFormState() {
  return {
    college_id: collegeSelect.value,
    target_ucs: getSelectedUcValues(),
    ge_pattern: geSelect.value,
    completed_courses: completedCoursesInput.value,
  };
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!isSubmitAllowed(plannerState)) {
    return;
  }

  hideApiError();
  renderSetupErrors([]);

  const formState = readCurrentFormState();
  setPlannerState(PlannerUiStates.LOADING);

  try {
    const outcome = processSetupSubmission(formState, {
      saveRequest: (payload) => {
        savePathwayRequest(payload);
      },
      navigate: (path) => {
        window.location.assign(path);
      },
    });

    if (!outcome.ok) {
      renderSetupErrors(outcome.errors);
      setPlannerState(PlannerUiStates.ERROR);
    }
  } catch {
    renderSetupErrors([
      {
        field: "form",
        message: "Unable to start pathway generation. Please try again.",
      },
    ]);
    setPlannerState(PlannerUiStates.ERROR);
  }
});

for (const el of [collegeSelect, ucSelect, geSelect, completedCoursesInput]) {
  el.addEventListener("input", () => {
    renderSetupErrors([]);
  });
  el.addEventListener("change", () => {
    renderSetupErrors([]);
  });
}

setSubmittingState(false);
hideApiError();
renderSetupErrors([]);
loadMetadata();
