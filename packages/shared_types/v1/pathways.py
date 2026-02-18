"""Versioned shared types and validation for v1 pathway APIs."""

from __future__ import annotations

from typing import Any, Iterable

API_VERSION = "v1"

# Defaults are fallback only; API should pass runtime-backed allowed values.
ALLOWED_COLLEGES = {"de_anza", "lassen"}
ALLOWED_UCS = {"UCLA", "UCSD", "UCM"}
ALLOWED_GE_PATTERNS = {"IGETC", "7CoursePattern"}
ALLOWED_WARNING_SEVERITIES = {"INFO", "WARN", "ERROR"}


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _normalize_details(details: Any) -> list[dict[str, str]]:
    if not isinstance(details, list):
        return []
    normalized: list[dict[str, str]] = []
    for item in details:
        if not isinstance(item, dict):
            continue
        field = str(item.get("field") or "").strip()
        message = str(item.get("message") or "").strip()
        if not field or not message:
            continue
        normalized.append({"field": field, "message": message})
    return sorted(normalized, key=lambda x: (x["field"], x["message"]))


def build_error_response(
    code: str,
    message: str,
    details: list[dict[str, str]] | None = None,
    *,
    status: int | None = None,
    request_id: str | None = None,
    path: str | None = None,
) -> dict[str, Any]:
    return {
        "version": API_VERSION,
        "request_id": request_id or "",
        "error": {
            "code": code,
            "message": message,
            "status": int(status or 500),
            "path": path or "",
            "details": _normalize_details(details or []),
        },
    }


def normalize_warning_payloads(
    warnings: Any,
    *,
    trace_id: str,
    default_source: str = "planner_core",
    default_severity: str = "WARN",
) -> list[dict[str, Any]]:
    if not isinstance(warnings, list):
        return []

    normalized: list[dict[str, Any]] = []
    for warning in warnings:
        if not isinstance(warning, dict):
            continue
        code = warning.get("code")
        message = warning.get("message")
        if not _is_non_empty_string(code) or not _is_non_empty_string(message):
            continue
        severity = str(warning.get("severity") or default_severity).upper()
        if severity not in ALLOWED_WARNING_SEVERITIES:
            severity = default_severity
        source = str(warning.get("source") or default_source)
        normalized.append(
            {
                "code": str(code),
                "message": str(message),
                "severity": severity,
                "source": source,
                "trace_id": str(warning.get("trace_id") or trace_id),
                "details": _normalize_details(warning.get("details")),
            }
        )

    return sorted(
        normalized,
        key=lambda x: (
            x["code"],
            x["message"],
            x["severity"],
            x["source"],
            x["trace_id"],
            tuple((d["field"], d["message"]) for d in x["details"]),
        ),
    )


def validate_generate_request(
    payload: Any,
    *,
    allowed_colleges: set[str] | None = None,
    allowed_ucs: set[str] | None = None,
    allowed_ge_patterns: set[str] | None = None,
) -> list[dict[str, str]]:
    """Validate request body for POST /v1/pathways/generate."""
    errors: list[dict[str, str]] = []
    colleges = allowed_colleges or ALLOWED_COLLEGES
    ucs = allowed_ucs or ALLOWED_UCS
    ge_patterns = allowed_ge_patterns or ALLOWED_GE_PATTERNS

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
    elif ge_pattern not in ge_patterns:
        errors.append(
            {
                "field": "ge_pattern",
                "message": f"ge_pattern must be one of: {sorted(ge_patterns)}.",
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


def validate_generate_response_shape(payload: Any) -> list[str]:
    """Used by tests to assert the POST /v1/pathways/generate response contract."""
    shape_errors: list[str] = []
    if not isinstance(payload, dict):
        return ["Response must be an object."]

    if payload.get("version") != API_VERSION:
        shape_errors.append("version must be 'v1'.")
    if not _is_non_empty_string(payload.get("request_id")):
        shape_errors.append("request_id must be a non-empty string.")

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
            if warning.get("severity") not in ALLOWED_WARNING_SEVERITIES:
                shape_errors.append(f"warnings[{i}].severity must be one of {sorted(ALLOWED_WARNING_SEVERITIES)}.")
            if not _is_non_empty_string(warning.get("source")):
                shape_errors.append(f"warnings[{i}].source must be a non-empty string.")
            if not _is_non_empty_string(warning.get("trace_id")):
                shape_errors.append(f"warnings[{i}].trace_id must be a non-empty string.")
            if not isinstance(warning.get("details"), list):
                shape_errors.append(f"warnings[{i}].details must be an array.")

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


def _validate_metadata_item(item: Any, kind: str, index: int) -> list[str]:
    errors: list[str] = []
    if not isinstance(item, dict):
        return [f"{kind}.data[{index}] must be an object."]
    if not _is_non_empty_string(item.get("id")):
        errors.append(f"{kind}.data[{index}].id must be a non-empty string.")
    if not _is_non_empty_string(item.get("name")):
        errors.append(f"{kind}.data[{index}].name must be a non-empty string.")
    return errors


def validate_metadata_response_shape(payload: Any, *, kind: str) -> list[str]:
    shape_errors: list[str] = []
    if not isinstance(payload, dict):
        return [f"{kind} response must be an object."]
    if payload.get("version") != API_VERSION:
        shape_errors.append(f"{kind}.version must be 'v1'.")
    data = payload.get("data")
    if not isinstance(data, list):
        shape_errors.append(f"{kind}.data must be an array.")
        return shape_errors
    for idx, item in enumerate(data):
        shape_errors.extend(_validate_metadata_item(item, kind, idx))
    return shape_errors


def validate_health_response_shape(payload: Any) -> list[str]:
    shape_errors: list[str] = []
    if not isinstance(payload, dict):
        return ["health response must be an object."]
    if payload.get("version") != API_VERSION:
        shape_errors.append("health.version must be 'v1'.")
    if payload.get("status") != "ok":
        shape_errors.append("health.status must be 'ok'.")
    runtime = payload.get("runtime")
    if not isinstance(runtime, dict):
        shape_errors.append("health.runtime must be an object.")
    else:
        if not _is_non_empty_string(runtime.get("dataset_version")):
            shape_errors.append("health.runtime.dataset_version must be a non-empty string.")
        if not _is_non_empty_string(runtime.get("generated_at")):
            shape_errors.append("health.runtime.generated_at must be a non-empty string.")
        if not isinstance(runtime.get("row_counts"), dict):
            shape_errors.append("health.runtime.row_counts must be an object.")
    return shape_errors


def validate_error_response_shape(payload: Any) -> list[str]:
    shape_errors: list[str] = []
    if not isinstance(payload, dict):
        return ["error response must be an object."]
    if payload.get("version") != API_VERSION:
        shape_errors.append("error.version must be 'v1'.")
    if not _is_non_empty_string(payload.get("request_id")):
        shape_errors.append("error.request_id must be a non-empty string.")
    error = payload.get("error")
    if not isinstance(error, dict):
        shape_errors.append("error payload must include an error object.")
        return shape_errors
    if not _is_non_empty_string(error.get("code")):
        shape_errors.append("error.code must be a non-empty string.")
    if not _is_non_empty_string(error.get("message")):
        shape_errors.append("error.message must be a non-empty string.")
    if not isinstance(error.get("status"), int):
        shape_errors.append("error.status must be an integer.")
    if not _is_non_empty_string(error.get("path")):
        shape_errors.append("error.path must be a non-empty string.")
    details = error.get("details")
    if not isinstance(details, list):
        shape_errors.append("error.details must be an array.")
    else:
        for i, detail in enumerate(details):
            if not isinstance(detail, dict):
                shape_errors.append(f"error.details[{i}] must be an object.")
                continue
            if not _is_non_empty_string(detail.get("field")):
                shape_errors.append(f"error.details[{i}].field must be a non-empty string.")
            if not _is_non_empty_string(detail.get("message")):
                shape_errors.append(f"error.details[{i}].message must be a non-empty string.")
    return shape_errors


def validate_metrics_response_shape(payload: Any) -> list[str]:
    shape_errors: list[str] = []
    if not isinstance(payload, dict):
        return ["metrics response must be an object."]
    if payload.get("version") != API_VERSION:
        shape_errors.append("metrics.version must be 'v1'.")
    if payload.get("sli") != "valid_request_success_rate":
        shape_errors.append("metrics.sli must be 'valid_request_success_rate'.")

    totals = payload.get("totals")
    if not isinstance(totals, dict):
        shape_errors.append("metrics.totals must be an object.")
    else:
        for key in (
            "request_count",
            "success_count",
            "error_count",
            "valid_request_count",
            "valid_success_count",
            "valid_error_count",
        ):
            if not isinstance(totals.get(key), int):
                shape_errors.append(f"metrics.totals.{key} must be an integer.")
        if not isinstance(totals.get("error_count_by_code"), dict):
            shape_errors.append("metrics.totals.error_count_by_code must be an object.")
        rate = totals.get("valid_success_rate")
        if rate is not None and not isinstance(rate, (int, float)):
            shape_errors.append("metrics.totals.valid_success_rate must be number or null.")

    by_route = payload.get("by_route")
    if not isinstance(by_route, list):
        shape_errors.append("metrics.by_route must be an array.")
    else:
        for i, item in enumerate(by_route):
            if not isinstance(item, dict):
                shape_errors.append(f"metrics.by_route[{i}] must be an object.")
                continue
            if not _is_non_empty_string(item.get("method")):
                shape_errors.append(f"metrics.by_route[{i}].method must be a non-empty string.")
            if not _is_non_empty_string(item.get("path")):
                shape_errors.append(f"metrics.by_route[{i}].path must be a non-empty string.")
            for key in (
                "request_count",
                "success_count",
                "error_count",
                "valid_request_count",
                "valid_success_count",
                "valid_error_count",
            ):
                if not isinstance(item.get(key), int):
                    shape_errors.append(f"metrics.by_route[{i}].{key} must be an integer.")
            if not isinstance(item.get("error_count_by_code"), dict):
                shape_errors.append(f"metrics.by_route[{i}].error_count_by_code must be an object.")
            rate = item.get("valid_success_rate")
            if rate is not None and not isinstance(rate, (int, float)):
                shape_errors.append(f"metrics.by_route[{i}].valid_success_rate must be number or null.")

    product = payload.get("product")
    if not isinstance(product, dict):
        shape_errors.append("metrics.product must be an object.")
        return shape_errors

    for key in (
        "pathway_generation_requests_total",
        "pathway_generation_valid_requests_total",
        "pathway_generation_success_total",
    ):
        if not isinstance(product.get(key), int):
            shape_errors.append(f"metrics.product.{key} must be an integer.")

    top_sets = product.get("top_target_uc_sets")
    if not isinstance(top_sets, list):
        shape_errors.append("metrics.product.top_target_uc_sets must be an array.")
    else:
        for i, item in enumerate(top_sets):
            if not isinstance(item, dict):
                shape_errors.append(f"metrics.product.top_target_uc_sets[{i}] must be an object.")
                continue
            if not isinstance(item.get("uc_targets"), list):
                shape_errors.append(
                    f"metrics.product.top_target_uc_sets[{i}].uc_targets must be an array."
                )
            else:
                for j, uc in enumerate(item.get("uc_targets")):
                    if not _is_non_empty_string(uc):
                        shape_errors.append(
                            f"metrics.product.top_target_uc_sets[{i}].uc_targets[{j}] must be non-empty string."
                        )
            if not isinstance(item.get("count"), int):
                shape_errors.append(f"metrics.product.top_target_uc_sets[{i}].count must be an integer.")

    ge_usage = product.get("ge_pattern_usage")
    if not isinstance(ge_usage, list):
        shape_errors.append("metrics.product.ge_pattern_usage must be an array.")
    else:
        for i, item in enumerate(ge_usage):
            if not isinstance(item, dict):
                shape_errors.append(f"metrics.product.ge_pattern_usage[{i}] must be an object.")
                continue
            if not _is_non_empty_string(item.get("ge_pattern")):
                shape_errors.append(
                    f"metrics.product.ge_pattern_usage[{i}].ge_pattern must be a non-empty string."
                )
            if not isinstance(item.get("count"), int):
                shape_errors.append(f"metrics.product.ge_pattern_usage[{i}].count must be an integer.")

    warnings = product.get("warnings")
    if not isinstance(warnings, dict):
        shape_errors.append("metrics.product.warnings must be an object.")
    else:
        if not isinstance(warnings.get("responses_with_warnings"), int):
            shape_errors.append("metrics.product.warnings.responses_with_warnings must be an integer.")
        rate = warnings.get("warning_rate")
        if rate is not None and not isinstance(rate, (int, float)):
            shape_errors.append("metrics.product.warnings.warning_rate must be number or null.")

    plan_shape = product.get("plan_shape")
    if not isinstance(plan_shape, dict):
        shape_errors.append("metrics.product.plan_shape must be an object.")
    else:
        avg_terms = plan_shape.get("average_terms_generated")
        if avg_terms is not None and not isinstance(avg_terms, (int, float)):
            shape_errors.append(
                "metrics.product.plan_shape.average_terms_generated must be number or null."
            )
        avg_courses = plan_shape.get("average_courses_per_term")
        if avg_courses is not None and not isinstance(avg_courses, (int, float)):
            shape_errors.append(
                "metrics.product.plan_shape.average_courses_per_term must be number or null."
            )

    latency_hist = product.get("latency_histogram_ms")
    if not isinstance(latency_hist, list):
        shape_errors.append("metrics.product.latency_histogram_ms must be an array.")
    else:
        for i, item in enumerate(latency_hist):
            if not isinstance(item, dict):
                shape_errors.append(f"metrics.product.latency_histogram_ms[{i}] must be an object.")
                continue
            if not _is_non_empty_string(item.get("bucket")):
                shape_errors.append(
                    f"metrics.product.latency_histogram_ms[{i}].bucket must be a non-empty string."
                )
            if not isinstance(item.get("count"), int):
                shape_errors.append(
                    f"metrics.product.latency_histogram_ms[{i}].count must be an integer."
                )
    return shape_errors


def sort_metadata_items(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for item in items:
        if not isinstance(item, dict):
            continue
        item_id = item.get("id")
        item_name = item.get("name")
        if not _is_non_empty_string(item_id) or not _is_non_empty_string(item_name):
            continue
        out.append({"id": str(item_id), "name": str(item_name)})
    return sorted(out, key=lambda x: (x["id"], x["name"]))
