from __future__ import annotations

import unittest
from pathlib import Path

from tests.golden.runner import load_scenarios, run_all


BASE_DIR = Path(__file__).resolve().parent
SCENARIOS_DIR = BASE_DIR / "scenarios"
EXPECTED_DIR = BASE_DIR / "expected"


class FullSuiteScenariosTests(unittest.TestCase):
    def test_full_suite_has_twenty_eight_scenarios(self):
        scenarios = load_scenarios(SCENARIOS_DIR, suite="full")
        self.assertEqual(len(scenarios), 28)

    def test_full_suite_is_deterministic_across_five_runs(self):
        baseline = run_all(SCENARIOS_DIR, EXPECTED_DIR, suite="full")
        for _ in range(4):
            self.assertEqual(run_all(SCENARIOS_DIR, EXPECTED_DIR, suite="full"), baseline)


if __name__ == "__main__":
    unittest.main()
