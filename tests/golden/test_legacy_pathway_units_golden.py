from __future__ import annotations

import importlib.util
import io
import json
import re
import unittest
from contextlib import redirect_stdout
from pathlib import Path


def _load_legacy_pathway_module():
    project_root = Path(__file__).resolve().parents[2]
    legacy_dir = project_root / "legacy" / "pathway_generator"
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


class LegacyPathwayUnitsGoldenTests(unittest.TestCase):
    def test_de_anza_ucla_ucsd_igetc_units_match_golden(self):
        module = _load_legacy_pathway_module()

        # Keep logs local to this invocation.
        if hasattr(module, "DEBUG_LOG"):
            module.DEBUG_LOG.clear()

        with redirect_stdout(io.StringIO()):
            paths = module.build_file_paths("de_anza", ["UCSD", "UCLA"])
            actual = module.generate_pathway(
                paths["articulated_courses_json"],
                paths["prereq_file"],
                paths["ge_reqs_json"],
                paths["course_reqs_json"],
                "de_anza",
                ["UCSD", "UCLA"],
                "IGETC",
            )

        expected_path = (
            Path(__file__).resolve().parent
            / "expected"
            / "legacy_de_anza_ucsd_ucla_igetc_expected.json"
        )
        expected = json.loads(expected_path.read_text(encoding="utf-8"))

        self.assertEqual(_canonicalize_plan(actual), _canonicalize_plan(expected))

        # Regression guard: all selected math courses in this scenario must be 5 units.
        for term in actual:
            for course in term.get("courses", []):
                code = str(course.get("courseCode", ""))
                if code.startswith("MATH "):
                    self.assertEqual(
                        course.get("units"),
                        5,
                        msg=f"Expected {code} to be 5 units, got {course.get('units')}",
                    )


if __name__ == "__main__":
    unittest.main()
