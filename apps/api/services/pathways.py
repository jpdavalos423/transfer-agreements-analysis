"""Pure pathway service layer used by API transport handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypedDict

from apps.api.planner_service import (
    PlannerServiceError as PlannerRuntimeError,
    generate_pathway_response,
)
from packages.shared_types.v1 import normalize_warning_payloads


@dataclass(frozen=True)
class GeneratePathwayInput:
    college_id: str
    target_ucs: tuple[str, ...]
    ge_pattern: str
    completed_courses: tuple[str, ...]
    request_id: str


class GeneratePathwayOutput(TypedDict, total=False):
    version: str
    request_id: str
    plan: list[dict[str, Any]]
    warnings: list[dict[str, Any]]
    meta: dict[str, Any]


class PathwayServiceError(RuntimeError):
    """Typed service-layer error for pathway generation."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        status: int,
        details: list[dict[str, str]] | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details or []


def _as_request_payload(data: GeneratePathwayInput) -> dict[str, Any]:
    return {
        "college_id": data.college_id,
        "target_ucs": list(data.target_ucs),
        "ge_pattern": data.ge_pattern,
        "completed_courses": list(data.completed_courses),
    }


def generate_pathway(
    data: GeneratePathwayInput,
    *,
    runtime_manifest: dict[str, Any],
) -> GeneratePathwayOutput:
    """Generate normalized v1 pathway response from validated request input."""
    payload = _as_request_payload(data)

    try:
        response = generate_pathway_response(payload)
    except PlannerRuntimeError as exc:
        raise PathwayServiceError(
            code="PLANNER_RUNTIME_ERROR",
            message="Unable to generate pathway response from runtime artifacts.",
            status=500,
            details=[{"field": "planner_service", "message": str(exc)}],
        ) from exc

    response.setdefault("meta", {})
    response["request_id"] = data.request_id
    response["warnings"] = normalize_warning_payloads(
        response.get("warnings"),
        trace_id=data.request_id,
        default_source="planner_core",
        default_severity="WARN",
    )
    response["meta"]["runtime"] = {
        "dataset_version": runtime_manifest.get("version"),
        "generated_at": runtime_manifest.get("generated_at"),
    }
    return response
