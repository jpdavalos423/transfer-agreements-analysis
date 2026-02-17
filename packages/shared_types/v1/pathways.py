"""Versioned shared types and validation for v1 pathway APIs."""

from __future__ import annotations

from typing import Any

API_VERSION = "v1"

# MVP subset defaults (may be overridden by loader-fed values in API).
ALLOWED_COLLEGES = {"de_anza", "lassen"}
ALLOWED_UCS = {"UCLA", "UCSD", "UCM"}
ALLOWED_GE_PATTERNS = {"IGETC", "7CoursePattern"}


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def validate_generate_request(
    payload: Any,
    *,
    allowed_colleges: set[str] | None = None,
    allowed_ucs: set[str] | None = None,
) -> list[dict[str, str]]:
    """Validate request body for POST /v1/pathways/generate."""
    errors: list[dict[str, str]] = []
    colleges = allowed_colleges or ALLOWED_COLLEGES
    ucs = allowed_ucs or ALLOWED_UCS

    if not isinstance(payload, dict):
        return [{"field": "body", "message": "Request body must be a JSON object."}]

    college_id = payload.get("college_id")
    if not _is_non_empty_string(college_id):
        errors.append({"field": "college_id", "message": "college_id is required and must be a non-empty string."})
    elif college_id not in colleges:
        errors.append(
            {
                "field": "college_id",
                "message": f"college_id must be one of: {sorted(colleges)}.",
            }
        )

    target_ucs = payload.get("target_ucs")
    if not isinstance(target_ucs, list) or len(target_ucs) == 0:
        errors.append({"field": "target_ucs", "message": "target_ucs is required and must be a non-empty array."})
    else:
        for idx, uc in enumerate(target_ucs):
            if not _is_non_empty_string(uc):
                errors.append({"field": f"target_ucs[{idx}]", "message": "Each target UC must be a non-empty string."})
            elif uc not in ucs:
                errors.append(
                    {
                        "field": f"target_ucs[{idx}]",
                        "message": f"UC must be one of: {sorted(ucs)}.",
                    }
                )

    ge_pattern = payload.get("ge_pattern")
    if not _is_non_empty_string(ge_pattern):
        errors.append({"field": "ge_pattern", "message": "ge_pattern is required and must be a non-empty string."})
    elif ge_pattern not in ALLOWED_GE_PATTERNS:
        errors.append(
            {
                "field": "ge_pattern",
                "message": f"ge_pattern must be one of: {sorted(ALLOWED_GE_PATTERNS)}.",
            }
        )

    completed_courses = payload.get("completed_courses")
    if completed_courses is None:
        errors.append({"field": "completed_courses", "message": "completed_courses is required and must be an array."})
    elif not isinstance(completed_courses, list):
        errors.append({"field": "completed_courses", "message": "completed_courses must be an array of strings."})
    else:
        for idx, course in enumerate(completed_courses):
            if not _is_non_empty_string(course):
                errors.append(
                    {
                        "field": f"completed_courses[{idx}]",
                        "message": "Each completed course must be a non-empty string.",
                    }
                )

    return errors


def build_error_response(code: str, message: str, details: list[dict[str, str]] | None = None) -> dict[str, Any]:
    return {
        "version": API_VERSION,
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
        },
    }


def validate_generate_response_shape(payload: Any) -> list[str]:
    """Used by tests to assert the response contract."""
    shape_errors: list[str] = []
    if not isinstance(payload, dict):
        return ["Response must be an object."]

    if payload.get("version") != API_VERSION:
        shape_errors.append("version must be 'v1'.")

    if not isinstance(payload.get("plan"), list):
        shape_errors.append("plan must be an array.")

    warnings = payload.get("warnings")
    if not isinstance(warnings, list):
        shape_errors.append("warnings must be an array.")
    else:
        for i, warning in enumerate(warnings):
            if not isinstance(warning, dict):
                shape_errors.append(f"warnings[{i}] must be an object.")
                continue
            if not _is_non_empty_string(warning.get("code")):
                shape_errors.append(f"warnings[{i}].code must be a non-empty string.")
            if not _is_non_empty_string(warning.get("message")):
                shape_errors.append(f"warnings[{i}].message must be a non-empty string.")

    meta = payload.get("meta")
    if not isinstance(meta, dict):
        shape_errors.append("meta must be an object.")
    else:
        if not _is_non_empty_string(meta.get("college_id")):
            shape_errors.append("meta.college_id must be a non-empty string.")
        if not isinstance(meta.get("target_ucs"), list):
            shape_errors.append("meta.target_ucs must be an array.")
        if not _is_non_empty_string(meta.get("ge_pattern")):
            shape_errors.append("meta.ge_pattern must be a non-empty string.")
        if not isinstance(meta.get("completed_courses_count"), int):
            shape_errors.append("meta.completed_courses_count must be an integer.")

    return shape_errors
