"""Planner execution service wiring runtime artifacts to planner_core."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from apps.api.runtime_data_loader import RuntimeDataError, load_runtime_data
from packages.planner_core import generate_plan_from_runtime_model, sort_generate_response
from packages.shared_types.v1 import API_VERSION


class PlannerServiceError(RuntimeError):
    """Raised when planner dependencies cannot be loaded or executed."""


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PlannerServiceError(f"Required planner input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PlannerServiceError(f"Invalid JSON in planner input file: {path}") from exc


@lru_cache(maxsize=1)
def _runtime_model():
    runtime_dir = _project_root() / "data" / "runtime"
    try:
        loaded = load_runtime_data(runtime_dir)
    except RuntimeDataError as exc:
        raise PlannerServiceError(str(exc)) from exc
    return loaded.model


@lru_cache(maxsize=1)
def _ge_data() -> dict[str, Any]:
    path = _project_root() / "prerequisites" / "ge_reqs.json"
    payload = _read_json(path)
    if not isinstance(payload, dict):
        raise PlannerServiceError(f"Expected object JSON in {path}")
    return payload


@lru_cache(maxsize=1)
def _course_reqs_data() -> dict[str, Any]:
    path = _project_root() / "scraping" / "files" / "course_reqs.json"
    payload = _read_json(path)
    if not isinstance(payload, dict):
        raise PlannerServiceError(f"Expected object JSON in {path}")
    return payload


def _prereq_filename_for_college(college_id: str) -> str | None:
    mapping = {
        "de_anza": "de_anza_college_prereqs.json",
        # Lassen prerequisite JSON is not yet available in source inputs.
        "lassen": None,
    }
    return mapping.get(college_id)


@lru_cache(maxsize=8)
def _prereq_records_for_college(college_id: str) -> Any:
    filename = _prereq_filename_for_college(college_id)
    if filename is None:
        return []
    path = _project_root() / "prerequisites" / filename
    payload = _read_json(path)
    if not isinstance(payload, list):
        raise PlannerServiceError(f"Expected array JSON in {path}")
    return payload


def generate_pathway_response(request_payload: dict[str, Any]) -> dict[str, Any]:
    """Generate a deterministic v1 response from runtime artifacts + planner_core."""
    try:
        response = generate_plan_from_runtime_model(
            college_id=str(request_payload["college_id"]),
            target_ucs=[str(uc) for uc in request_payload["target_ucs"]],
            ge_pattern=str(request_payload["ge_pattern"]),
            completed_courses=[str(c) for c in request_payload["completed_courses"]],
            runtime_model=_runtime_model(),
            prereq_records=_prereq_records_for_college(str(request_payload["college_id"])),
            ge_data=_ge_data(),
            course_reqs_data=_course_reqs_data(),
        )
    except KeyError as exc:
        raise PlannerServiceError(f"Missing required request field: {exc}") from exc
    except PlannerServiceError:
        raise
    except Exception as exc:  # pragma: no cover - defensive API boundary
        raise PlannerServiceError(f"Planner execution failed: {exc}") from exc

    response["version"] = API_VERSION
    return sort_generate_response(response)

