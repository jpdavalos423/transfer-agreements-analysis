import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { fetchColleges, fetchUcs } from "../api/client";
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

function readSelectedValues(select: HTMLSelectElement): string[] {
  return Array.from(select.selectedOptions).map((option) => option.value);
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

  useEffect(() => {
    let active = true;

    async function loadMetadata() {
      setIsMetadataLoading(true);
      setMetadataError("");
      try {
        const [collegePayload, ucPayload] = await Promise.all([fetchColleges(), fetchUcs()]);
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

  function onUcChange(select: HTMLSelectElement) {
    clearErrors();
    setFormState((prev) => ({ ...prev, target_ucs: readSelectedValues(select) }));
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
    <main className="container">
      <a className="skip-link" href="#planner-setup-form">
        Skip to planner setup form
      </a>
      <h1>Transfer Pathway Planner</h1>
      <p className="subtle">React + Vite parallel app (migration path)</p>

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
          <select
            id="target_ucs"
            name="target_ucs"
            value={formState.target_ucs}
            onChange={(event) => onUcChange(event.currentTarget)}
            disabled={isMetadataLoading || isSubmitting}
            multiple
            size={Math.max(3, Math.min(8, ucs.length || 3))}
            required
            aria-describedby="target-ucs-help"
            aria-invalid={validationErrors.some((error) => error.field === "target_ucs")}
          >
            {ucs.map((uc) => (
              <option key={uc.id} value={uc.id}>
                {uc.name}
              </option>
            ))}
          </select>
          <small id="target-ucs-help">Hold Ctrl/Cmd to select multiple</small>
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
