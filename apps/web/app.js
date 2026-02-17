const API_URL = "http://127.0.0.1:8000/v1/pathways/generate";

const form = document.getElementById("planner-form");
const warningsList = document.getElementById("warnings-list");
const responseJson = document.getElementById("response-json");

function parseCompletedCourses(text) {
  return text
    .split(/\r?\n|,/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}

function getSelectedValues(selectEl) {
  return Array.from(selectEl.selectedOptions).map((opt) => opt.value);
}

function renderWarnings(warnings) {
  warningsList.innerHTML = "";
  if (!Array.isArray(warnings) || warnings.length === 0) {
    const li = document.createElement("li");
    li.textContent = "No warnings.";
    warningsList.appendChild(li);
    return;
  }

  warnings.forEach((warning) => {
    const li = document.createElement("li");
    const code = warning?.code || "UNKNOWN";
    const message = warning?.message || "Unknown warning.";
    li.textContent = `${code}: ${message}`;
    warningsList.appendChild(li);
  });
}

async function submitPlannerRequest(payload) {
  const resp = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await resp.json();
  if (!resp.ok) {
    throw data;
  }
  return data;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    college_id: document.getElementById("college_id").value.trim(),
    target_ucs: getSelectedValues(document.getElementById("target_ucs")),
    ge_pattern: document.getElementById("ge_pattern").value,
    completed_courses: parseCompletedCourses(document.getElementById("completed_courses").value),
  };

  responseJson.textContent = "Loading...";
  warningsList.innerHTML = "";

  try {
    const data = await submitPlannerRequest(payload);
    renderWarnings(data.warnings || []);
    responseJson.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    const fallback = {
      version: "v1",
      error: err?.error || {
        code: "REQUEST_FAILED",
        message: "Unable to reach API endpoint.",
        details: [],
      },
    };
    renderWarnings([{ code: fallback.error.code, message: fallback.error.message }]);
    responseJson.textContent = JSON.stringify(fallback, null, 2);
  }
});

