import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { generatePathway, mapApiErrorToUiState } from "../api/client";
import { GeneratePathwayRequest, GeneratePathwayResponse } from "../types";
import { loadPathwayRequest } from "../utils/pathwayRequestStorage";
import { ResultsView } from "./ResultsView";
import { StatusPanel } from "./StatusPanel";

type PathwayUiState = "idle" | "loading" | "success" | "error";

type PathwayPageProps = {
  loadStoredRequest?: () => GeneratePathwayRequest | null;
  requestPathway?: (
    payload: GeneratePathwayRequest,
  ) => Promise<GeneratePathwayResponse>;
};

export function PathwayPage({
  loadStoredRequest = loadPathwayRequest,
  requestPathway = generatePathway,
}: PathwayPageProps) {
  const [uiState, setUiState] = useState<PathwayUiState>("idle");
  const [payload, setPayload] = useState<GeneratePathwayRequest | null>(null);
  const [response, setResponse] = useState<GeneratePathwayResponse | null>(null);
  const [error, setError] = useState<ReturnType<typeof mapApiErrorToUiState> | null>(null);
  const inFlightRef = useRef(false);

  const hasPayload = payload !== null;

  const runRequest = useCallback(async (requestPayload: GeneratePathwayRequest) => {
    if (inFlightRef.current) {
      return;
    }

    inFlightRef.current = true;
    setUiState("loading");
    setError(null);
    setResponse(null);

    try {
      const apiResponse = await requestPathway(requestPayload);
      setResponse(apiResponse);
      setUiState("success");
    } catch (err) {
      setError(mapApiErrorToUiState(err));
      setUiState("error");
    } finally {
      inFlightRef.current = false;
    }
  }, [requestPathway]);

  useEffect(() => {
    const storedPayload = loadStoredRequest();
    if (!storedPayload) {
      setUiState("idle");
      return;
    }

    setPayload(storedPayload);
    void runRequest(storedPayload);
  }, [loadStoredRequest, runRequest]);

  const canRetry = useMemo(
    () => hasPayload && (uiState === "idle" || uiState === "error"),
    [hasPayload, uiState],
  );

  async function handleRetry() {
    if (!payload) {
      return;
    }
    await runRequest(payload);
  }

  return (
    <main className="container">
      <a className="skip-link" href="#pathway-content-anchor">
        Skip to pathway content
      </a>
      <h1>Your Transfer Pathway</h1>
      <p className="subtle">
        <Link to="/">Back to setup form</Link>
      </p>

      {uiState === "idle" ? (
        <section className="panel" aria-live="polite" role="status">
          <h2>No pathway request found</h2>
          <p>Submit the planner form first to generate your pathway.</p>
          <p>
            <Link to="/">Go to setup form</Link>
          </p>
        </section>
      ) : null}

      {uiState === "loading" ? (
        <section className="panel" aria-live="polite" role="status" aria-busy="true">
          <h2>Generating pathway...</h2>
          <p>Please wait while we load your pathway.</p>
        </section>
      ) : null}

      {uiState === "error" && error ? (
        <section className="panel panel-error" aria-live="assertive" role="alert">
          <h2>Request Error</h2>
          <p>
            {error.code}: {error.message}
          </p>
          {error.details.length > 0 ? (
            <ul className="status-list">
              {error.details.map((detail, index) => (
                <li key={`${detail.field}-${index}`}>
                  {detail.field}: {detail.message}
                </li>
              ))}
            </ul>
          ) : null}
          <div className="pathway-actions">
            <button type="button" onClick={() => void handleRetry()} disabled={!canRetry}>
              Retry
            </button>
            <Link to="/">Back to form</Link>
          </div>
        </section>
      ) : null}

      {uiState === "success" && response ? (
        <div id="pathway-content-anchor" className="results-layout">
          <StatusPanel response={response} />
          <section className="panel" aria-live="polite">
            <h2>Pathway Results</h2>
            <ResultsView response={response} />
          </section>
        </div>
      ) : null}
    </main>
  );
}
