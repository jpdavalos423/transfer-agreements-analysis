from __future__ import annotations

from typing import Any

from .sort_utils import sort_generate_response


def generate_stub_plan(request_payload: dict[str, Any]) -> dict[str, Any]:
    """
    Temporary planner output used for vertical-slice and golden harness wiring.
    This is intentionally not full planner logic.
    """
    response = {
        "version": "v1",
        "plan": [],
        "warnings": [
            {
                "code": "PLANNER_NOT_IMPLEMENTED",
                "message": "Planner logic is not implemented yet; returning stub response.",
            }
        ],
        "meta": {
            "college_id": request_payload["college_id"],
            "target_ucs": request_payload["target_ucs"],
            "ge_pattern": request_payload["ge_pattern"],
            "completed_courses_count": len(request_payload["completed_courses"]),
        },
    }
    return sort_generate_response(response)

