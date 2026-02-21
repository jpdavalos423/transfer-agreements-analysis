import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { getColleges, getUcs } from "../api/client";
import { MetadataItem } from "../types";
import {
  SetupFormState,
  ValidationIssue,
  buildGeneratePayload,
  validateSetupInput,
} from "../utils/plannerForm";
import { savePathwayRequest } from "../utils/pathwayRequestStorage";

const INITIAL_FORM_STATE: SetupFormState = {
  college_id: "",
  target_ucs: [],
  ge_pattern: "IGETC",
  completed_courses: "",
};

const UC_ID_ORDER = ["UCB", "UCD", "UCI", "UCLA", "UCM", "UCR", "UCSB", "UCSC", "UCSD"] as const;

const UC_BRAND: Record<string, { name: string; mascot: string; logoPath: string }> = {
  UCB: {
    name: "UC Berkeley",
    mascot: "Golden Bears",
    logoPath: "/uc-mascots/ucb.webp",
  },
  UCD: {
    name: "UC Davis",
    mascot: "Aggies",
    logoPath: "/uc-mascots/ucd.webp",
  },
  UCI: {
    name: "UC Irvine",
    mascot: "Anteaters",
    logoPath: "/uc-mascots/uci.webp",
  },
  UCLA: {
    name: "UCLA",
    mascot: "Bruins",
    logoPath: "/uc-mascots/ucla.webp",
  },
  UCM: {
    name: "UC Merced",
    mascot: "Bobcats",
    logoPath: "/uc-mascots/ucm.webp",
  },
  UCR: {
    name: "UC Riverside",
    mascot: "Highlanders",
    logoPath: "/uc-mascots/ucr.webp",
  },
  UCSB: {
    name: "UC Santa Barbara",
    mascot: "Gauchos",
    logoPath: "/uc-mascots/ucsb.webp",
  },
  UCSC: {
    name: "UC Santa Cruz",
    mascot: "Banana Slugs",
    logoPath: "/uc-mascots/ucsc.webp",
  },
  UCSD: {
    name: "UC San Diego",
    mascot: "Tritons",
    logoPath: "/uc-mascots/ucsd.webp",
  },
};

type UcButtonOption = {
  id: string;
  name: string;
  mascot: string;
  logoUrl: string;
  available: boolean;
};

function buildUcButtonOptions(ucs: MetadataItem[]): UcButtonOption[] {
  const availableById = new Map(ucs.map((item) => [item.id, item]));

  const canonical = UC_ID_ORDER.map((id) => ({
    id,
    name: UC_BRAND[id]?.name || availableById.get(id)?.name || id,
    mascot: UC_BRAND[id]?.mascot || "Mascot",
    logoUrl: UC_BRAND[id]?.logoPath || "/uc-mascots/ucsd.webp",
    available: availableById.has(id),
  }));

  const extras = ucs
    .filter((item) => !UC_ID_ORDER.includes(item.id as (typeof UC_ID_ORDER)[number]))
    .map((item) => ({
      id: item.id,
      name: item.name || item.id,
      mascot: "Mascot",
      logoUrl: "/uc-mascots/ucsd.webp",
      available: true,
    }));

  return [...canonical, ...extras];
}

export function SetupPage() {
  const navigate = useNavigate();

  const [colleges, setColleges] = useState<MetadataItem[]>([]);
  const [ucs, setUcs] = useState<MetadataItem[]>([]);
  const [isMetadataLoading, setIsMetadataLoading] = useState(true);
  const [metadataError, setMetadataError] = useState<string>("");

  const [formState, setFormState] = useState<SetupFormState>(INITIAL_FORM_STATE);
  const [validationErrors, setValidationErrors] = useState<ValidationIssue[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [requestError, setRequestError] = useState<string>("");
  const [failedUcLogos, setFailedUcLogos] = useState<Record<string, boolean>>({});

  useEffect(() => {
    let active = true;

    async function loadMetadata() {
      setIsMetadataLoading(true);
      setMetadataError("");
      try {
        const [collegePayload, ucPayload] = await Promise.all([getColleges(), getUcs()]);
        if (!active) {
          return;
        }

        setColleges(Array.isArray(collegePayload?.data) ? collegePayload.data : []);
        setUcs(Array.isArray(ucPayload?.data) ? ucPayload.data : []);
      } catch {
        if (!active) {
          return;
        }
        setMetadataError("Failed to load setup options.");
      } finally {
        if (active) {
          setIsMetadataLoading(false);
        }
      }
    }

    void loadMetadata();
    return () => {
      active = false;
    };
  }, []);

  const canSubmit = useMemo(() => !isMetadataLoading && !isSubmitting, [isMetadataLoading, isSubmitting]);
  const hasTargetUcError = useMemo(
    () => validationErrors.some((error) => error.field === "target_ucs"),
    [validationErrors],
  );
  const ucButtonOptions = useMemo(() => buildUcButtonOptions(ucs), [ucs]);
  const unavailableUcCount = useMemo(
    () => ucButtonOptions.filter((option) => !option.available).length,
    [ucButtonOptions],
  );

  function clearErrors() {
    if (validationErrors.length > 0) {
      setValidationErrors([]);
    }
    if (requestError) {
      setRequestError("");
    }
  }

  function onCollegeChange(value: string) {
    clearErrors();
    setFormState((prev) => ({ ...prev, college_id: value }));
  }

  function onUcToggle(ucId: string) {
    clearErrors();
    setFormState((prev) => {
      const isSelected = prev.target_ucs.includes(ucId);
      if (isSelected) {
        return { ...prev, target_ucs: prev.target_ucs.filter((id) => id !== ucId) };
      }
      return { ...prev, target_ucs: [...prev.target_ucs, ucId] };
    });
  }

  function markLogoFailed(ucId: string) {
    setFailedUcLogos((prev) => {
      if (prev[ucId]) {
        return prev;
      }
      return { ...prev, [ucId]: true };
    });
  }

  function onGePatternChange(value: string) {
    clearErrors();
    setFormState((prev) => ({ ...prev, ge_pattern: value }));
  }

  function onCompletedCoursesChange(value: string) {
    clearErrors();
    setFormState((prev) => ({ ...prev, completed_courses: value }));
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }

    clearErrors();
    setIsSubmitting(true);

    try {
      const payload = buildGeneratePayload(formState);
      const errors = validateSetupInput(payload);
      if (errors.length > 0) {
        setValidationErrors(errors);
        return;
      }

      savePathwayRequest(payload);
      navigate("/pathway");
    } catch {
      setRequestError("Unable to start pathway generation. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="container setup-container">
      <a className="skip-link" href="#planner-setup-form">
        Skip to planner setup form
      </a>
      <h1>Transfer Pathway Planner</h1>
      <p className="subtle">For California CC to UC transfer planning</p>

      {metadataError ? (
        <section className="panel panel-error" aria-live="assertive" role="alert">
          <h2>Setup Error</h2>
          <p>{metadataError}</p>
          <p className="subtle">
            Confirm the API is running, then refresh this page.
          </p>
        </section>
      ) : null}

      <form
        id="planner-setup-form"
        className="panel"
        onSubmit={onSubmit}
        noValidate
        aria-busy={isSubmitting}
        aria-describedby={
          validationErrors.length > 0
            ? "setup-validation-errors"
            : requestError
              ? "setup-request-error"
              : undefined
        }
      >
        <div className="field">
          <label htmlFor="college_id">College</label>
          <select
            id="college_id"
            name="college_id"
            value={formState.college_id}
            onChange={(event) => onCollegeChange(event.currentTarget.value)}
            disabled={isMetadataLoading || isSubmitting}
            aria-invalid={validationErrors.some((error) => error.field === "college_id")}
            required
          >
            <option value="">{isMetadataLoading ? "Loading colleges..." : "Select a college..."}</option>
            {colleges.map((college) => (
              <option key={college.id} value={college.id}>
                {college.name}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="target_ucs">Target UCs</label>
          <input
            id="target_ucs"
            name="target_ucs"
            className="sr-only-input"
            value={formState.target_ucs.join(",")}
            readOnly
            aria-hidden="true"
            tabIndex={-1}
          />
          <div
            className={`uc-selector${hasTargetUcError ? " has-error" : ""}`}
            role="group"
            aria-describedby="target-ucs-help"
            aria-invalid={hasTargetUcError}
          >
            <div className="uc-selector-row uc-selector-row-5">
              {ucButtonOptions.slice(0, 5).map((uc) => {
                const isSelected = formState.target_ucs.includes(uc.id);
                const isDisabled = isMetadataLoading || isSubmitting || !uc.available;
                return (
                  <button
                    key={uc.id}
                    type="button"
                    className={`uc-card${isSelected ? " is-selected" : ""}`}
                    onClick={() => onUcToggle(uc.id)}
                    disabled={isDisabled}
                    aria-pressed={isSelected}
                    aria-label={uc.name}
                    title={`${uc.name} ${uc.mascot}`}
                  >
                    {failedUcLogos[uc.id] ? (
                      <span className="uc-card-fallback" aria-hidden="true">
                        {uc.id}
                      </span>
                    ) : (
                      <img
                        className="uc-card-logo"
                        src={uc.logoUrl}
                        alt=""
                        aria-hidden="true"
                        onError={() => markLogoFailed(uc.id)}
                      />
                    )}
                    <span className="uc-card-code">{uc.id}</span>
                    <span className="uc-card-mascot">{uc.mascot}</span>
                  </button>
                );
              })}
            </div>
            <div className="uc-selector-row uc-selector-row-4">
              {ucButtonOptions.slice(5).map((uc) => {
                const isSelected = formState.target_ucs.includes(uc.id);
                const isDisabled = isMetadataLoading || isSubmitting || !uc.available;
                return (
                  <button
                    key={uc.id}
                    type="button"
                    className={`uc-card${isSelected ? " is-selected" : ""}`}
                    onClick={() => onUcToggle(uc.id)}
                    disabled={isDisabled}
                    aria-pressed={isSelected}
                    aria-label={uc.name}
                    title={`${uc.name} ${uc.mascot}`}
                  >
                    {failedUcLogos[uc.id] ? (
                      <span className="uc-card-fallback" aria-hidden="true">
                        {uc.id}
                      </span>
                    ) : (
                      <img
                        className="uc-card-logo"
                        src={uc.logoUrl}
                        alt=""
                        aria-hidden="true"
                        onError={() => markLogoFailed(uc.id)}
                      />
                    )}
                    <span className="uc-card-code">{uc.id}</span>
                    <span className="uc-card-mascot">{uc.mascot}</span>
                  </button>
                );
              })}
            </div>
          </div>
          <small id="target-ucs-help" className="uc-selector-help">
            Select one or more UCs.
          </small>
          {!isMetadataLoading && unavailableUcCount > 0 ? (
            <small className="subtle uc-selector-help">
              Some UC options are disabled because they are unavailable in the current runtime dataset.
            </small>
          ) : null}
        </div>

        <div className="field">
          <label htmlFor="ge_pattern">GE Pattern</label>
          <select
            id="ge_pattern"
            name="ge_pattern"
            value={formState.ge_pattern}
            onChange={(event) => onGePatternChange(event.currentTarget.value)}
            disabled={isSubmitting}
            aria-invalid={validationErrors.some((error) => error.field === "ge_pattern")}
            required
          >
            <option value="IGETC">IGETC</option>
            <option value="7CoursePattern">7CoursePattern</option>
          </select>
        </div>

        <div className="field">
          <label htmlFor="completed_courses">Completed Courses (one per line)</label>
          <textarea
            id="completed_courses"
            name="completed_courses"
            rows={6}
            value={formState.completed_courses}
            onChange={(event) => onCompletedCoursesChange(event.currentTarget.value)}
            placeholder={"MATH 1A\nCIS 22A"}
            disabled={isSubmitting}
          />
        </div>

        <button type="submit" disabled={!canSubmit}>
          {isSubmitting ? "Continuing..." : "Generate Pathway"}
        </button>
      </form>

      {validationErrors.length > 0 ? (
        <section id="setup-validation-errors" className="panel panel-error" aria-live="assertive" role="alert">
          <h2>Form Validation</h2>
          <ul className="status-list">
            {validationErrors.map((error, index) => (
              <li key={`${error.field}-${index}`}>{error.message}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {requestError ? (
        <section id="setup-request-error" className="panel panel-error" aria-live="assertive" role="alert">
          <h2>Request Error</h2>
          <p>{requestError}</p>
        </section>
      ) : null}

      <section className="panel">
        <h2>Navigation</h2>
        <p className="subtle">
          Already generated a pathway? <Link to="/pathway">Go to pathway page</Link>
        </p>
      </section>
    </main>
  );
}
