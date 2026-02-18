from __future__ import annotations

import ast
import importlib.util
import io
import json
import re
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from packages.planner_core import generate_plan_from_runtime


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_legacy_pathway_module():
    legacy_dir = REPO_ROOT / "pathway_generator"
    module_path = legacy_dir / "pathway_generator.py"

    import sys

    if str(legacy_dir) not in sys.path:
        sys.path.insert(0, str(legacy_dir))

    spec = importlib.util.spec_from_file_location("legacy_pathway_generator", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module spec from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _term_sort_key(term_name: str) -> tuple[int, str]:
    match = re.search(r"\d+", term_name or "")
    return (int(match.group(0)), term_name) if match else (10_000, term_name or "")


def _canonicalize_plan(plan: list[dict]) -> list[dict]:
    normalized_terms: list[dict] = []
    for term in plan:
        courses = term.get("courses", [])
        normalized_courses = sorted(
            [
                {"courseCode": c.get("courseCode"), "units": c.get("units")}
                for c in courses
            ],
            key=lambda c: (str(c.get("courseCode", "")), c.get("units", 0)),
        )
        normalized_terms.append({"term": term.get("term"), "courses": normalized_courses})

    return sorted(normalized_terms, key=lambda t: _term_sort_key(str(t.get("term", ""))))


def _load_runtime_rows() -> tuple[list[dict], list[dict]]:
    filtered = json.loads((REPO_ROOT / "data" / "runtime" / "filtered_rows.json").read_text(encoding="utf-8"))
    district = json.loads((REPO_ROOT / "data" / "runtime" / "district_rows.json").read_text(encoding="utf-8"))
    return filtered, district


def _load_ge_data() -> dict:
    return json.loads((REPO_ROOT / "prerequisites" / "ge_reqs.json").read_text(encoding="utf-8"))


def _load_course_reqs() -> dict:
    return json.loads((REPO_ROOT / "scraping" / "files" / "course_reqs.json").read_text(encoding="utf-8"))


def _load_de_anza_prereqs() -> list[dict]:
    return json.loads((REPO_ROOT / "prerequisites" / "de_anza_college_prereqs.json").read_text(encoding="utf-8"))


class PurePlannerParityTests(unittest.TestCase):
    def _run_legacy(self, *, uc_list: list[str], ge_pattern: str) -> list[dict]:
        legacy = _load_legacy_pathway_module()
        if hasattr(legacy, "DEBUG_LOG"):
            legacy.DEBUG_LOG.clear()

        art_path = REPO_ROOT / "articulated_courses_json" / "De_Anza_College_articulation.json"
        prereq_path = REPO_ROOT / "prerequisites" / "de_anza_college_prereqs.json"
        ge_path = REPO_ROOT / "prerequisites" / "ge_reqs.json"
        major_path = REPO_ROOT / "scraping" / "files" / "course_reqs.json"

        with redirect_stdout(io.StringIO()):
            return legacy.generate_pathway(
                art_path,
                prereq_path,
                ge_path,
                major_path,
                "de_anza",
                uc_list,
                ge_pattern,
            )

    def _run_pure(self, *, uc_list: list[str], ge_pattern: str) -> dict:
        filtered_rows, district_rows = _load_runtime_rows()
        return generate_plan_from_runtime(
            college_id="de_anza",
            target_ucs=uc_list,
            ge_pattern=ge_pattern,
            completed_courses=[],
            filtered_rows=filtered_rows,
            district_rows=district_rows,
            prereq_records=_load_de_anza_prereqs(),
            ge_data=_load_ge_data(),
            course_reqs_data=_load_course_reqs(),
        )

    def test_parity_de_anza_ucla_ucsd_igetc(self):
        legacy_plan = self._run_legacy(uc_list=["UCSD", "UCLA"], ge_pattern="IGETC")
        pure_plan = self._run_pure(uc_list=["UCSD", "UCLA"], ge_pattern="IGETC")["plan"]
        self.assertEqual(_canonicalize_plan(pure_plan), _canonicalize_plan(legacy_plan))

    def test_parity_de_anza_ucm_igetc(self):
        legacy_plan = self._run_legacy(uc_list=["UCM"], ge_pattern="IGETC")
        pure_plan = self._run_pure(uc_list=["UCM"], ge_pattern="IGETC")["plan"]
        self.assertEqual(_canonicalize_plan(pure_plan), _canonicalize_plan(legacy_plan))

    def test_deterministic_across_five_runs(self):
        baseline = self._run_pure(uc_list=["UCSD", "UCLA"], ge_pattern="IGETC")["plan"]
        baseline_c = _canonicalize_plan(baseline)
        for _ in range(4):
            current = self._run_pure(uc_list=["UCSD", "UCLA"], ge_pattern="IGETC")["plan"]
            self.assertEqual(_canonicalize_plan(current), baseline_c)

    def test_pure_planner_module_has_no_open_calls(self):
        source_path = REPO_ROOT / "packages" / "planner_core" / "pure_planner.py"
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        open_calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
                open_calls.append((node.lineno, node.col_offset))
        self.assertEqual(open_calls, [])


if __name__ == "__main__":
    unittest.main()
