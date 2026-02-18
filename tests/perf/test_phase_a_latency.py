from __future__ import annotations

import unittest
from pathlib import Path

from tests.perf.latency_runner import format_summary, measure_latency


BASE_DIR = Path(__file__).resolve().parents[2]
SCENARIOS_DIR = BASE_DIR / "tests" / "golden" / "scenarios"


class PhaseALatencyTests(unittest.TestCase):
    def test_phase_a_p95_under_two_seconds(self):
        summary = measure_latency(
            scenarios_dir=SCENARIOS_DIR,
            suite="phase_a",
            repeat=3,
            warmup=1,
            threshold_seconds=2.0,
        )
        self.assertGreaterEqual(len(summary.scenarios), 8)
        self.assertTrue(summary.passes_threshold, msg=format_summary(summary))


if __name__ == "__main__":
    unittest.main()

