from __future__ import annotations

import json
import unittest
from pathlib import Path

from apps.api.runtime_data_loader import load_runtime_data
from packages.planner_core import generate_plan_from_runtime_model


REPO_ROOT = Path(__file__).resolve().parents[2]


class PlannerRuntimeLoaderE2ETests(unittest.TestCase):
    def test_load_runtime_then_generate_plan(self):
        runtime = load_runtime_data(REPO_ROOT / "data" / "runtime")
        prereqs = json.loads((REPO_ROOT / "prerequisites" / "de_anza_college_prereqs.json").read_text(encoding="utf-8"))
        ge_data = json.loads((REPO_ROOT / "prerequisites" / "ge_reqs.json").read_text(encoding="utf-8"))
        course_reqs = json.loads((REPO_ROOT / "scraping" / "files" / "course_reqs.json").read_text(encoding="utf-8"))

        result = generate_plan_from_runtime_model(
            college_id="de_anza",
            target_ucs=["UCSD", "UCLA"],
            ge_pattern="IGETC",
            completed_courses=[],
            runtime_model=runtime.model,
            prereq_records=prereqs,
            ge_data=ge_data,
            course_reqs_data=course_reqs,
        )

        self.assertIsInstance(result, dict)
        self.assertIsInstance(result.get("plan"), list)
        self.assertGreater(len(result["plan"]), 0)
        self.assertEqual(result["meta"]["college_id"], "de_anza")
        self.assertEqual(result["meta"]["runtime_manifest_version"], runtime.model.manifest["version"])


if __name__ == "__main__":
    unittest.main()
