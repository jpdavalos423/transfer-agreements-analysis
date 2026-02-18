from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from apps.api.planner_service import generate_pathway_response
from packages.planner_core import canonicalize_for_comparison

from .comparator import semantic_compare


@dataclass(frozen=True)
class GoldenScenario:
    scenario_id: str
    description: str
    request: dict[str, Any]
    expected_file: str
    tags: tuple[str, ...] = ()


def load_scenarios(
    scenarios_dir: str | Path,
    suite: str | None = None,
) -> list[GoldenScenario]:
    path = Path(scenarios_dir)
    scenarios: list[GoldenScenario] = []
    for scenario_file in sorted(path.glob("*.json"), key=lambda p: p.name):
        payload = json.loads(scenario_file.read_text(encoding="utf-8"))
        tags = tuple(payload.get("tags") or ())
        if suite and suite != "all" and suite not in tags:
            continue
        scenarios.append(
            GoldenScenario(
                scenario_id=payload["id"],
                description=payload.get("description", ""),
                request=payload["request"],
                expected_file=payload["expected_file"],
                tags=tags,
            )
        )
    return scenarios


def run_scenario(scenario: GoldenScenario, expected_dir: str | Path) -> dict[str, Any]:
    expected_path = Path(expected_dir) / scenario.expected_file
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    actual = generate_pathway_response(scenario.request)

    ok, diff = semantic_compare(actual, expected)
    if not ok:
        raise AssertionError(
            f"Golden mismatch for scenario '{scenario.scenario_id}'.\n"
            f"Description: {scenario.description}\n{diff}"
        )

    return canonicalize_for_comparison(actual)


def run_all(
    scenarios_dir: str | Path,
    expected_dir: str | Path,
    suite: str | None = None,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for scenario in load_scenarios(scenarios_dir, suite=suite):
        results.append(run_scenario(scenario, expected_dir))
    return results
