import {
  buildGeneratePayload,
  extractApiError,
  validateSetupInput,
} from "./planner_form.js";
import { renderResults } from "./results_view.js";
import { renderStatusPanel } from "./status_panel.js";

const API_BASE_URL = "http://127.0.0.1:8000";
const GENERATE_URL = `${API_BASE_URL}/v1/pathways/generate`;
const COLLEGES_URL = `${API_BASE_URL}/v1/metadata/colleges`;
const UCS_URL = `${API_BASE_URL}/v1/metadata/ucs`;

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
const confidenceLabel = document.getElementById("confidence-label");
const warningsList = document.getElementById("warnings-list");
const unmetSection = document.getElementById("unmet-section");
const unmetList = document.getElementById("unmet-list");
const responseJson = document.getElementById("response-json");
const resultsContent = document.getElementById("results-content");
const statusElements = {
  confidenceLabel,
  warningsList,
  unmetSection,
  unmetList,
};

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

function renderApiError(errorPayload) {
  const { code, message, details } = extractApiError(errorPayload);
  apiErrorHeadline.textContent = `${code}: ${message}`;
  clearElementChildren(apiErrorDetails);
  for (const detail of details) {
    const li = document.createElement("li");
    li.textContent = `${detail.field}: ${detail.message}`;
    apiErrorDetails.appendChild(li);
  }
  apiErrorPanel.hidden = false;
}

function hideApiError() {
  apiErrorPanel.hidden = true;
  apiErrorHeadline.textContent = "";
  clearElementChildren(apiErrorDetails);
}

function renderResultsPlaceholder(message) {
  if (!resultsContent) {
    return;
  }
  resultsContent.innerHTML = "";
  const p = document.createElement("p");
  p.className = "results-placeholder";
  p.textContent = message;
  resultsContent.appendChild(p);
}

async function fetchJson(url) {
  const response = await fetch(url, { method: "GET" });
  const payload = await response.json();
  if (!response.ok) {
    throw payload;
  }
  return payload;
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

async function submitPlannerRequest(payload) {
  const response = await fetch(GENERATE_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const responsePayload = await response.json();
  if (!response.ok) {
    throw responsePayload;
  }
  return responsePayload;
}

async function loadMetadata() {
  setSelectLoading(collegeSelect, "Loading colleges...");
  setSelectLoading(ucSelect, "Loading UCs...");

  try {
    const [collegesPayload, ucsPayload] = await Promise.all([
      fetchJson(COLLEGES_URL),
      fetchJson(UCS_URL),
    ]);
    const colleges = Array.isArray(collegesPayload?.data)
      ? collegesPayload.data
      : [];
    const ucs = Array.isArray(ucsPayload?.data) ? ucsPayload.data : [];

    populateCollegeOptions(colleges);
    populateUcOptions(ucs);
  } catch (errorPayload) {
    setSelectError(collegeSelect, "Unable to load colleges.");
    setSelectError(ucSelect, "Unable to load UC options.");
    renderApiError(errorPayload);
    responseJson.textContent = JSON.stringify(errorPayload, null, 2);
    renderResultsPlaceholder("Results will appear after a successful generation.");
  }
}

function setSubmittingState(isSubmitting) {
  submitButton.disabled = isSubmitting;
  submitButton.textContent = isSubmitting
    ? "Generating..."
    : "Generate Pathway";
}

function buildCurrentPayload() {
  return buildGeneratePayload({
    college_id: collegeSelect.value,
    target_ucs: getSelectedUcValues(),
    ge_pattern: geSelect.value,
    completed_courses: completedCoursesInput.value,
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideApiError();
  renderSetupErrors([]);

  const payload = buildCurrentPayload();
  const validationErrors = validateSetupInput(payload);
  if (validationErrors.length > 0) {
    renderSetupErrors(validationErrors);
    return;
  }

  setSubmittingState(true);
  responseJson.textContent = "Loading...";
  renderStatusPanel(statusElements, { plan: [], warnings: [] });
  renderResultsPlaceholder("Generating pathway...");

  try {
    const data = await submitPlannerRequest(payload);
    renderStatusPanel(statusElements, data);
    responseJson.textContent = JSON.stringify(data, null, 2);
    renderResults(resultsContent, data);
  } catch (errorPayload) {
    renderStatusPanel(statusElements, { plan: [], warnings: [] });
    renderApiError(errorPayload);
    responseJson.textContent = JSON.stringify(errorPayload, null, 2);
    renderResultsPlaceholder("Results will appear after a successful generation.");
  } finally {
    setSubmittingState(false);
  }
});

renderResultsPlaceholder("Results will appear after a successful generation.");
renderStatusPanel(statusElements, { plan: [], warnings: [] });
loadMetadata();
