from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from apps.api.planner_service import generate_pathway_response
from packages.planner_core import canonicalize_for_comparison

from .comparator import semantic_compare
from .runner import GoldenScenario, load_scenarios


ResponseProvider = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class DeterminismSummary:
    suite: str
    repeat: int
    scenario_count: int


def _truncate_json(value: Any, *, limit: int = 240) -> str:
    text = json.dumps(value, sort_keys=True, ensure_ascii=False)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _first_mismatch_path(
    expected: Any,
    actual: Any,
    *,
    path: str = "$",
) -> tuple[str, Any, Any]:
    if type(expected) is not type(actual):
        return path, expected, actual

    if isinstance(expected, dict):
        keys = sorted(set(expected.keys()) | set(actual.keys()))
        for key in keys:
            has_expected = key in expected
            has_actual = key in actual
            child_path = f"{path}.{key}"
            if has_expected != has_actual:
                return child_path, expected.get(key), actual.get(key)
            mismatch = _first_mismatch_path(
                expected[key],
                actual[key],
                path=child_path,
            )
            if mismatch[0] is not None:
                return mismatch
        return None, None, None

    if isinstance(expected, list):
        if len(expected) != len(actual):
            return f"{path}.length", len(expected), len(actual)
        for idx, (e_item, a_item) in enumerate(zip(expected, actual)):
            mismatch = _first_mismatch_path(
                e_item,
                a_item,
                path=f"{path}[{idx}]",
            )
            if mismatch[0] is not None:
                return mismatch
        return None, None, None

    if expected != actual:
        return path, expected, actual
    return None, None, None


def _compare_or_raise(
    *,
    scenario: GoldenScenario,
    run_index: int,
    baseline: dict[str, Any],
    current: dict[str, Any],
) -> None:
    ok, diff = semantic_compare(current, baseline)
    if ok:
        return

    mismatch_path, expected_value, actual_value = _first_mismatch_path(baseline, current)
    path_display = mismatch_path or "$"
    raise AssertionError(
        (
            f"Determinism mismatch for scenario '{scenario.scenario_id}' "
            f"(run {run_index}).\n"
            f"Unstable path: {path_display}\n"
            f"Expected: {_truncate_json(expected_value)}\n"
            f"Actual: {_truncate_json(actual_value)}\n"
            f"Semantic diff:\n{diff}"
        )
    )


def run_determinism_suite(
    *,
    scenarios_dir: str | Path,
    suite: str = "full",
    repeat: int = 10,
    response_provider: ResponseProvider = generate_pathway_response,
) -> DeterminismSummary:
    if repeat < 2:
        raise ValueError("repeat must be >= 2")

    scenarios = load_scenarios(scenarios_dir, suite=suite)
    if not scenarios:
        raise ValueError(f"No scenarios selected for suite '{suite}'.")

    for scenario in scenarios:
        baseline = canonicalize_for_comparison(response_provider(dict(scenario.request)))
        for run_index in range(2, repeat + 1):
            current = canonicalize_for_comparison(response_provider(dict(scenario.request)))
            _compare_or_raise(
                scenario=scenario,
                run_index=run_index,
                baseline=baseline,
                current=current,
            )

    return DeterminismSummary(
        suite=suite,
        repeat=repeat,
        scenario_count=len(scenarios),
    )

