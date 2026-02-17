from __future__ import annotations

import unittest
from pathlib import Path

from tests.golden.runner import load_scenarios, run_scenario


BASE_DIR = Path(__file__).resolve().parent
SCENARIOS_DIR = BASE_DIR / "scenarios"
EXPECTED_DIR = BASE_DIR / "expected"
PHASE_A_PREFIX = "phase_a_"


def _run_phase_a_once() -> list[dict]:
    scenarios = [
        scenario
        for scenario in load_scenarios(SCENARIOS_DIR)
        if scenario.scenario_id.startswith(PHASE_A_PREFIX)
    ]
    results = [run_scenario(scenario, EXPECTED_DIR) for scenario in scenarios]
    return results


class PhaseAScenariosTests(unittest.TestCase):
    def test_phase_a_has_eight_scenarios_and_all_pass(self):
        scenarios = [
            scenario
            for scenario in load_scenarios(SCENARIOS_DIR)
            if scenario.scenario_id.startswith(PHASE_A_PREFIX)
        ]
        self.assertEqual(len(scenarios), 8)
        for scenario in scenarios:
            result = run_scenario(scenario, EXPECTED_DIR)
            self.assertEqual(result.get("version"), "v1")

    def test_phase_a_is_deterministic_across_five_runs(self):
        baseline = _run_phase_a_once()
        for _ in range(4):
            self.assertEqual(_run_phase_a_once(), baseline)


if __name__ == "__main__":
    unittest.main()
