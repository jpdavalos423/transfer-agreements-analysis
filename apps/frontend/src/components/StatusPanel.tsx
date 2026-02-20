import { GeneratePathwayResponse } from "../types";
import {
  deriveConfidenceLabel,
  normalizeUnmetRequirements,
  normalizeWarnings,
} from "../utils/statusPanel";

interface Props {
  response: GeneratePathwayResponse;
}

function confidenceClassName(label: string): string {
  return `confidence-label confidence-${label.toLowerCase().replace(/\s+/g, "-")}`;
}

export function StatusPanel({ response }: Props) {
  const warnings = normalizeWarnings(Array.isArray(response?.warnings) ? response.warnings : []);
  const confidenceLabel = deriveConfidenceLabel(response);
  const unmetRequirements = normalizeUnmetRequirements(response?.unmet_requirements);

  return (
    <section className="panel" aria-live="polite">
      <h2>Plan Status</h2>
      <p className="confidence-row">
        Confidence: <span className={confidenceClassName(confidenceLabel)}>{confidenceLabel}</span>
      </p>

      <h3>Warnings</h3>
      {warnings.length === 0 ? (
        <ul className="status-list">
          <li>No warnings.</li>
        </ul>
      ) : (
        <ul className="status-list">
          {warnings.map((warning, index) => {
            const line = `[${warning.severity}] ${warning.message}`;
            return (
              <li key={`${warning.severity}-${warning.message}-${index}`}>
                {warning.context ? `${line} (${warning.context})` : line}
              </li>
            );
          })}
        </ul>
      )}

      {unmetRequirements.length > 0 ? (
        <div className="unmet-section">
          <h3>Unmet Requirements</h3>
          <ul className="status-list">
            {unmetRequirements.map((item, index) => (
              <li key={`${item}-${index}`}>{item}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
