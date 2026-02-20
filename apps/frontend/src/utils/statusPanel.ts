import { GeneratePathwayResponse, WarningItem } from "../types";

export type ConfidenceLabel =
  | "Complete with no warnings"
  | "Complete with caveats"
  | "Incomplete";

export interface NormalizedWarning {
  severity: string;
  message: string;
  context: string;
}

function isTrue(value: unknown): boolean {
  return value === true;
}

function hasExplicitIncomplete(response: GeneratePathwayResponse): boolean {
  if (isTrue(response.incomplete)) {
    return true;
  }
  if (isTrue(response?.meta?.incomplete)) {
    return true;
  }
  if (response.completion_flags && typeof response.completion_flags === "object") {
    if (response.completion_flags.complete === false) {
      return true;
    }
    if (response.completion_flags.is_complete === false) {
      return true;
    }
  }
  if (typeof response.completion_status === "string") {
    if (response.completion_status.toLowerCase() === "incomplete") {
      return true;
    }
  }
  return false;
}

export function deriveConfidenceLabel(response: GeneratePathwayResponse): ConfidenceLabel {
  const plan = Array.isArray(response.plan) ? response.plan : [];
  const warnings = Array.isArray(response.warnings) ? response.warnings : [];

  if (hasExplicitIncomplete(response) || plan.length === 0) {
    return "Incomplete";
  }
  if (warnings.length === 0) {
    return "Complete with no warnings";
  }
  return "Complete with caveats";
}

function normalizeWarningSeverity(value: unknown): string {
  if (typeof value !== "string" || value.trim() === "") {
    return "WARN";
  }
  return value.trim().toUpperCase();
}

function formatWarningContext(warning: WarningItem): string {
  const details = Array.isArray(warning?.details) ? warning.details : [];
  const detailParts = details
    .filter((item) => item && typeof item.field === "string" && typeof item.message === "string")
    .map((item) => `${item.field}: ${item.message}`);

  if (detailParts.length > 0) {
    return detailParts.join("; ");
  }
  if (typeof warning?.source === "string" && warning.source.trim() !== "") {
    return `source: ${warning.source}`;
  }
  return "";
}

function stableStringifyObject(value: unknown): string {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return JSON.stringify(value);
  }
  const sorted: Record<string, unknown> = {};
  for (const key of Object.keys(value as Record<string, unknown>).sort()) {
    sorted[key] = (value as Record<string, unknown>)[key];
  }
  return JSON.stringify(sorted);
}

function formatUnmetRequirement(item: unknown): string {
  if (typeof item === "string" && item.trim() !== "") {
    return item;
  }
  if (!item || typeof item !== "object") {
    return "";
  }

  const candidate = item as Record<string, unknown>;
  const primary =
    candidate.name ||
    candidate.requirement ||
    candidate.title ||
    candidate.group ||
    candidate.id ||
    "";

  const pieces: string[] = [];
  if (typeof primary === "string" && primary.trim() !== "") {
    pieces.push(primary.trim());
  }

  if (candidate.courses_remaining != null) {
    pieces.push(`courses remaining: ${String(candidate.courses_remaining)}`);
  } else if (candidate.remaining != null) {
    pieces.push(`remaining: ${String(candidate.remaining)}`);
  }

  if (typeof candidate.message === "string" && candidate.message.trim() !== "") {
    pieces.push(candidate.message.trim());
  }

  if (pieces.length > 0) {
    return pieces.join(" | ");
  }

  return stableStringifyObject(candidate);
}

export function normalizeWarnings(warnings: WarningItem[]): NormalizedWarning[] {
  const deduped = new Set<string>();
  const out: NormalizedWarning[] = [];

  for (const warning of warnings || []) {
    const normalized: NormalizedWarning = {
      severity: normalizeWarningSeverity(warning?.severity),
      message:
        typeof warning?.message === "string" && warning.message.trim() !== ""
          ? warning.message
          : "Unknown warning.",
      context: formatWarningContext(warning),
    };
    const dedupeKey = `${normalized.severity}|${normalized.message}|${normalized.context}`;
    if (deduped.has(dedupeKey)) {
      continue;
    }
    deduped.add(dedupeKey);
    out.push(normalized);
  }

  return out;
}

export function normalizeUnmetRequirements(items: unknown[] | undefined): string[] {
  const unmetRaw = Array.isArray(items) ? items : [];
  return unmetRaw
    .map((item) => formatUnmetRequirement(item))
    .filter((line) => line.length > 0);
}
