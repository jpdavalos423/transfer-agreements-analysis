from __future__ import annotations

import unittest
from pathlib import Path

from tests.golden.runner import load_scenarios, run_all


BASE_DIR = Path(__file__).resolve().parent
SCENARIOS_DIR = BASE_DIR / "scenarios"
EXPECTED_DIR = BASE_DIR / "expected"


class GoldenRunnerTests(unittest.TestCase):
    def test_golden_scenarios_pass(self):
        scenarios = load_scenarios(SCENARIOS_DIR)
        self.assertGreaterEqual(len(scenarios), 1)
        outputs = run_all(SCENARIOS_DIR, EXPECTED_DIR)
        self.assertEqual(len(outputs), len(scenarios))
        self.assertEqual(outputs[0]["version"], "v1")

    def test_deterministic_across_five_repeated_runs(self):
        baseline = run_all(SCENARIOS_DIR, EXPECTED_DIR)
        for _ in range(4):
            self.assertEqual(run_all(SCENARIOS_DIR, EXPECTED_DIR), baseline)


if __name__ == "__main__":
    unittest.main()
