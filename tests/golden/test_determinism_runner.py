from __future__ import annotations

import itertools
import unittest
from pathlib import Path

from tests.golden.determinism_runner import run_determinism_suite


BASE_DIR = Path(__file__).resolve().parent
SCENARIOS_DIR = BASE_DIR / "scenarios"


class DeterminismRunnerTests(unittest.TestCase):
    def test_phase_a_determinism_ten_runs(self):
        summary = run_determinism_suite(
            scenarios_dir=SCENARIOS_DIR,
            suite="phase_a",
            repeat=10,
        )
        self.assertEqual(summary.suite, "phase_a")
        self.assertEqual(summary.repeat, 10)
        self.assertEqual(summary.scenario_count, 8)

    def test_seeded_nondeterminism_is_detected_with_path(self):
        counter = itertools.count(1)

        def unstable_provider(_request: dict):
            n = next(counter)
            return {
                "version": "v1",
                "warnings": [],
                "plan": [{"term": "Term 1", "courses": [{"courseCode": "X", "units": 3}]}],
                "meta": {
                    "college_id": "de_anza",
                    "target_ucs": ["UCLA"],
                    "ge_pattern": "IGETC",
                    "completed_courses_count": 0,
                    # Intentionally unstable field for test-only injection.
                    "unstable_counter": n,
                },
            }

        with self.assertRaises(AssertionError) as ctx:
            run_determinism_suite(
                scenarios_dir=SCENARIOS_DIR,
                suite="phase_a",
                repeat=3,
                response_provider=unstable_provider,
            )

        message = str(ctx.exception)
        self.assertIn("Determinism mismatch", message)
        self.assertIn("Unstable path: $.meta.unstable_counter", message)


if __name__ == "__main__":
    unittest.main()

