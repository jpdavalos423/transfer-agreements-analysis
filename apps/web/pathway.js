import { createPathwayPageController } from "./pathway_page.js";
import { renderResults } from "./results_view.js";
import { renderStatusPanel } from "./status_panel.js";

const emptyState = document.getElementById("pathway-empty-state");
const loadingState = document.getElementById("pathway-loading-state");
const errorPanel = document.getElementById("pathway-error-panel");
const errorHeadline = document.getElementById("pathway-error-headline");
const errorDetails = document.getElementById("pathway-error-details");
const retryButton = document.getElementById("pathway-retry-button");
const contentPanel = document.getElementById("pathway-content");
const resultsContent = document.getElementById("results-content");

const statusElements = {
  confidenceLabel: document.getElementById("confidence-label"),
  warningsList: document.getElementById("warnings-list"),
  unmetSection: document.getElementById("unmet-section"),
  unmetList: document.getElementById("unmet-list"),
};

function setHidden(el, hidden) {
  if (!el) {
    return;
  }
  el.hidden = hidden;
}

function clearElementChildren(el) {
  if (!el) {
    return;
  }
  el.innerHTML = "";
}

function renderError(error) {
  if (!error) {
    errorHeadline.textContent = "";
    clearElementChildren(errorDetails);
    return;
  }
  errorHeadline.textContent = `${error.code}: ${error.message}`;
  clearElementChildren(errorDetails);
  for (const detail of error.details || []) {
    const li = document.createElement("li");
    li.textContent = `${detail.field}: ${detail.message}`;
    errorDetails.appendChild(li);
  }
}

function renderState(state) {
  const hasPayload = state.hasPayload;
  const showIdle = !hasPayload;
  const showLoading = hasPayload && state.plannerState === "loading";
  const showSuccess = hasPayload && state.plannerState === "success";
  const showError = hasPayload && state.plannerState === "error";

  setHidden(emptyState, !showIdle);
  setHidden(loadingState, !showLoading);
  setHidden(contentPanel, !showSuccess);
  setHidden(errorPanel, !showError);

  retryButton.disabled = state.isLoading;

  if (showSuccess) {
    renderStatusPanel(statusElements, state.data || { plan: [], warnings: [] });
    renderResults(resultsContent, state.data || { plan: [] });
  }

  if (showError) {
    renderError(state.error);
  }
}

const controller = createPathwayPageController({ onStateChange: renderState });
retryButton.addEventListener("click", async () => {
  await controller.retry();
});

controller.initialize();
