from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from apps.api.planner_service import generate_pathway_response
from packages.planner_core import canonicalize_for_comparison


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "golden_update"


class GoldenUpdateScriptTests(unittest.TestCase):
    def test_candidate_then_explicit_promote(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            scenarios_dir = tmp_path / "scenarios"
            expected_dir = tmp_path / "expected"
            candidate_dir = tmp_path / "_candidate"
            scenarios_dir.mkdir(parents=True, exist_ok=True)
            expected_dir.mkdir(parents=True, exist_ok=True)

            scenario = {
                "id": "tmp_phase_a_one",
                "description": "tmp scenario",
                "tags": ["phase_a", "full"],
                "request": {
                    "college_id": "de_anza",
                    "target_ucs": ["UCLA"],
                    "ge_pattern": "IGETC",
                    "completed_courses": ["MATH 1A"],
                },
                "expected_file": "tmp_phase_a_one_expected.json",
            }
            (scenarios_dir / "tmp_phase_a_one.json").write_text(
                json.dumps(scenario, indent=2) + "\n", encoding="utf-8"
            )

            # Seed expected with intentionally different payload so candidate diff is non-empty.
            bad_expected = canonicalize_for_comparison(generate_pathway_response(scenario["request"]))
            bad_expected["meta"]["completed_courses_count"] = 999
            (expected_dir / scenario["expected_file"]).write_text(
                json.dumps(bad_expected, indent=2) + "\n", encoding="utf-8"
            )

            candidate_cmd = [
                str(SCRIPT),
                "candidate",
                "--suite",
                "phase_a",
                "--scenario-id",
                "tmp_phase_a_one",
                "--scenarios-dir",
                str(scenarios_dir),
                "--expected-dir",
                str(expected_dir),
                "--candidate-dir",
                str(candidate_dir),
            ]
            candidate_run = subprocess.run(
                candidate_cmd,
                cwd=str(REPO_ROOT),
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(candidate_run.returncode, 0, msg=candidate_run.stderr)
            self.assertIn("[CHANGED] tmp_phase_a_one", candidate_run.stdout)
            candidate_file = candidate_dir / scenario["expected_file"]
            self.assertTrue(candidate_file.exists())

            # Without --yes, promotion should not write files.
            promote_preview_cmd = [
                str(SCRIPT),
                "promote",
                "--suite",
                "phase_a",
                "--scenario-id",
                "tmp_phase_a_one",
                "--scenarios-dir",
                str(scenarios_dir),
                "--expected-dir",
                str(expected_dir),
                "--candidate-dir",
                str(candidate_dir),
            ]
            preview_run = subprocess.run(
                promote_preview_cmd,
                cwd=str(REPO_ROOT),
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(preview_run.returncode, 2)
            self.assertIn("Re-run with --yes", preview_run.stdout)

            # With --yes, candidate should be promoted.
            promote_apply_cmd = promote_preview_cmd + ["--yes"]
            apply_run = subprocess.run(
                promote_apply_cmd,
                cwd=str(REPO_ROOT),
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(apply_run.returncode, 0, msg=apply_run.stderr)

            promoted_expected = (expected_dir / scenario["expected_file"]).read_text(
                encoding="utf-8"
            )
            promoted_candidate = candidate_file.read_text(encoding="utf-8")
            self.assertEqual(promoted_expected, promoted_candidate)


if __name__ == "__main__":
    unittest.main()
