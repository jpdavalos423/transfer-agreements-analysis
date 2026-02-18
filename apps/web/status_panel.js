function isNonEmptyArray(value) {
  return Array.isArray(value) && value.length > 0;
}

function toBoolean(value) {
  return value === true;
}

function hasExplicitIncomplete(responsePayload) {
  if (!responsePayload || typeof responsePayload !== "object") {
    return false;
  }
  if (toBoolean(responsePayload.incomplete)) {
    return true;
  }
  if (toBoolean(responsePayload?.meta?.incomplete)) {
    return true;
  }
  if (responsePayload?.completion_flags && typeof responsePayload.completion_flags === "object") {
    if (responsePayload.completion_flags.complete === false) {
      return true;
    }
    if (responsePayload.completion_flags.is_complete === false) {
      return true;
    }
  }
  if (typeof responsePayload?.completion_status === "string") {
    if (responsePayload.completion_status.toLowerCase() === "incomplete") {
      return true;
    }
  }
  return false;
}

export function deriveConfidenceLabel(responsePayload) {
  const plan = Array.isArray(responsePayload?.plan) ? responsePayload.plan : [];
  const warnings = Array.isArray(responsePayload?.warnings)
    ? responsePayload.warnings
    : [];

  if (hasExplicitIncomplete(responsePayload) || plan.length === 0) {
    return "Incomplete";
  }
  if (warnings.length === 0) {
    return "Complete with no warnings";
  }
  return "Complete with caveats";
}

function formatWarningContext(warning) {
  const details = Array.isArray(warning?.details) ? warning.details : [];
  const detailParts = details
    .filter(
      (item) =>
        item &&
        typeof item === "object" &&
        typeof item.field === "string" &&
        typeof item.message === "string"
    )
    .map((item) => `${item.field}: ${item.message}`);
  if (detailParts.length > 0) {
    return detailParts.join("; ");
  }
  if (typeof warning?.source === "string" && warning.source.trim() !== "") {
    return `source: ${warning.source}`;
  }
  return "";
}

function formatUnmetRequirement(item) {
  if (typeof item === "string" && item.trim() !== "") {
    return item;
  }
  if (!item || typeof item !== "object") {
    return "";
  }

  const primary =
    item.name ||
    item.requirement ||
    item.title ||
    item.group ||
    item.id ||
    "";
  const pieces = [];
  if (typeof primary === "string" && primary.trim() !== "") {
    pieces.push(primary.trim());
  }

  if (item.courses_remaining != null) {
    pieces.push(`courses remaining: ${item.courses_remaining}`);
  } else if (item.remaining != null) {
    pieces.push(`remaining: ${item.remaining}`);
  }

  if (typeof item.message === "string" && item.message.trim() !== "") {
    pieces.push(item.message.trim());
  }

  if (pieces.length > 0) {
    return pieces.join(" | ");
  }
  return JSON.stringify(item);
}

export function buildStatusViewModel(responsePayload) {
  const confidenceLabel = deriveConfidenceLabel(responsePayload);
  const warningsRaw = Array.isArray(responsePayload?.warnings)
    ? responsePayload.warnings
    : [];
  const warnings = warningsRaw.map((warning) => ({
    severity:
      typeof warning?.severity === "string" && warning.severity.trim() !== ""
        ? warning.severity
        : "WARN",
    message:
      typeof warning?.message === "string" && warning.message.trim() !== ""
        ? warning.message
        : "Unknown warning.",
    context: formatWarningContext(warning),
  }));

  const unmetRaw = Array.isArray(responsePayload?.unmet_requirements)
    ? responsePayload.unmet_requirements
    : [];
  const unmetRequirements = unmetRaw
    .map((item) => formatUnmetRequirement(item))
    .filter((line) => line.length > 0);

  return {
    confidenceLabel,
    warnings,
    hasWarnings: isNonEmptyArray(warnings),
    unmetRequirements,
    hasUnmetRequirements: isNonEmptyArray(unmetRequirements),
  };
}

export function renderStatusPanel(elements, responsePayload) {
  const model = buildStatusViewModel(responsePayload);
  if (!elements || typeof elements !== "object") {
    return;
  }

  const confidenceLabel = elements.confidenceLabel;
  const warningsList = elements.warningsList;
  const unmetSection = elements.unmetSection;
  const unmetList = elements.unmetList;

  if (confidenceLabel) {
    confidenceLabel.textContent = model.confidenceLabel;
    confidenceLabel.className = `confidence-label confidence-${model.confidenceLabel
      .toLowerCase()
      .replace(/\s+/g, "-")}`;
  }

  if (warningsList) {
    warningsList.innerHTML = "";
    if (!model.hasWarnings) {
      const li = document.createElement("li");
      li.textContent = "No warnings.";
      warningsList.appendChild(li);
    } else {
      for (const warning of model.warnings) {
        const li = document.createElement("li");
        const base = `[${warning.severity}] ${warning.message}`;
        li.textContent = warning.context ? `${base} (${warning.context})` : base;
        warningsList.appendChild(li);
      }
    }
  }

  if (unmetSection && unmetList) {
    unmetList.innerHTML = "";
    if (!model.hasUnmetRequirements) {
      unmetSection.hidden = true;
      return;
    }
    unmetSection.hidden = false;
    for (const unmet of model.unmetRequirements) {
      const li = document.createElement("li");
      li.textContent = unmet;
      unmetList.appendChild(li);
    }
  }
}

