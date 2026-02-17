from __future__ import annotations

import copy
from typing import Any


def _normalize_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _sort_warning_items(warnings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for w in warnings:
        if not isinstance(w, dict):
            continue
        normalized.append(
            {
                "code": w.get("code"),
                "message": w.get("message"),
            }
        )
    return sorted(normalized, key=lambda x: ((x.get("code") or ""), (x.get("message") or "")))


def _sort_courses(courses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for c in courses:
        if not isinstance(c, dict):
            continue
        entry = dict(c)
        if isinstance(entry.get("tags"), list):
            entry["tags"] = sorted(entry["tags"])
        if isinstance(entry.get("fulfills"), list):
            entry["fulfills"] = sorted(entry["fulfills"])
        normalized.append(entry)
    return sorted(
        normalized,
        key=lambda x: (
            str(x.get("courseCode") or ""),
            str(x.get("units") if x.get("units") is not None else ""),
        ),
    )


def _sort_plan(plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized_terms = []
    for idx, term in enumerate(plan):
        if not isinstance(term, dict):
            continue
        term_name = term.get("term")
        if not isinstance(term_name, str) or not term_name.strip():
            term_name = f"term_{idx}"
        normalized_terms.append(
            {
                "term": term_name,
                "courses": _sort_courses(_normalize_list(term.get("courses"))),
            }
        )
    return sorted(normalized_terms, key=lambda t: t["term"])


def sort_generate_response(response: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic ordering for planner outputs."""
    out = copy.deepcopy(response)
    out["warnings"] = _sort_warning_items(_normalize_list(out.get("warnings")))
    out["plan"] = _sort_plan(_normalize_list(out.get("plan")))
    meta = out.get("meta")
    if isinstance(meta, dict):
        target_ucs = meta.get("target_ucs")
        if isinstance(target_ucs, list):
            meta["target_ucs"] = sorted({str(v) for v in target_ucs})
    return out


def canonicalize_for_comparison(response: dict[str, Any]) -> dict[str, Any]:
    """
    Canonical form used by semantic comparator.
    Rules:
    - warning order ignored (compare sorted by code/message)
    - target_ucs order ignored (compare sorted unique values)
    - plan term order ignored (compare by normalized term key)
    - course order within term ignored (compare sorted by courseCode/units)
    """
    return sort_generate_response(response)

