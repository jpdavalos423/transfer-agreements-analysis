from __future__ import annotations

import json
import unittest
from pathlib import Path

from apps.api.runtime_data_loader import load_runtime_data
from packages.planner_core.pure_planner import (
    _MajorRequirements,
    _add_missing_prereqs,
    _build_articulated_from_rows,
    _build_uc_group_block_map_data,
    _get_unlocker_courses,
    _select_courses_for_term,
    generate_plan_from_runtime_model,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_course_reqs() -> dict:
    return json.loads((REPO_ROOT / "scraping" / "files" / "course_reqs.json").read_text(encoding="utf-8"))


def _load_prereqs_de_anza() -> list[dict]:
    return json.loads((REPO_ROOT / "prerequisites" / "de_anza_college_prereqs.json").read_text(encoding="utf-8"))


def _load_ge_data() -> dict:
    return json.loads((REPO_ROOT / "prerequisites" / "ge_reqs.json").read_text(encoding="utf-8"))


class LockedSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = load_runtime_data(REPO_ROOT / "data" / "runtime")
        cls.course_reqs = _load_course_reqs()
        cls.prereqs = _load_prereqs_de_anza()
        cls.ge_data = _load_ge_data()

    def test_or_of_and_articulation_logic_preserved(self):
        # Uses real normalized rows for de_anza + UCLA and asserts the Calc2 group
        # keeps multiple AND blocks (OR-of-AND structure).
        selected_rows = [
            {
                "source_file": r.source_file,
                "row_number": r.row_number,
                "mode": r.mode,
                "college_name": r.college_name,
                "uc_name": r.uc_name,
                "group_id": r.group_id,
                "set_id": r.set_id,
                "num_required": r.num_required,
                "receiving_raw": r.receiving_raw,
                "receiving_courses": list(r.receiving_courses),
                "articulation_status": r.articulation_status,
                "alternatives": [
                    {
                        "block_index": b.block_index,
                        "courses": [{"course_code": c.course_code, "units": c.units} for c in b.courses],
                    }
                    for b in r.alternatives
                ],
            }
            for r in self.runtime.model.filtered_rows
            if r.uc_name == "UCLA"
            and Path(r.source_file).name == "De_Anza_College_filtered.csv"
        ]

        articulated = _build_articulated_from_rows(
            college_id="de_anza",
            target_ucs=["UCLA"],
            selected_rows=selected_rows,
        )
        group_block_map, _ = _build_uc_group_block_map_data(
            college_id="de_anza",
            selected_ucs=["UCLA"],
            course_reqs_data=self.course_reqs,
            articulated=articulated,
        )

        calc2_blocks = group_block_map[("UCLA", "Calc2")]
        # Expect multiple alternatives (OR) and each is a 2-course block (AND).
        self.assertGreaterEqual(len(calc2_blocks), 2)
        self.assertTrue(all(len(block) == 2 for block in calc2_blocks))

    def test_distinct_row_instance_cardinality_enforced(self):
        # Internal assertion hook: group requires 2 distinct block instances.
        # Not directly observable in public output schema.
        major = _MajorRequirements(
            group_defs={"UCX": {"GroupA": {"courses": ["R1"], "num_required": 2}}},
            group_block_map={("UCX", "GroupA"): [["A"], ["B"], ["C"]]},
        )
        one_done = major.get_remaining_courses({"A"}, articulated={})
        two_done = major.get_remaining_courses({"A", "B"}, articulated={})
        self.assertGreater(len(one_done), 0)
        self.assertEqual(two_done, [])

    def test_honors_base_equivalence_retained_globally(self):
        # Internal assertion hook: selecting base marks honors equivalent complete.
        completed: set[str] = set()
        selected, _, _ = _select_courses_for_term(
            candidates=[
                {"courseCode": "MATH 1A", "units": 5},
                {"courseCode": "MATH 1AH", "units": 5},
            ],
            completed=completed,
            uc_to_cc_map={},
            all_cc_course_codes={"MATH 1A", "MATH 1AH"},
            max_units=16,
        )
        selected_codes = [c["courseCode"] for c in selected]
        self.assertIn("MATH 1A", selected_codes)
        self.assertNotIn("MATH 1AH", selected_codes)
        self.assertIn("MATH 1AH", completed)

    def test_direct_prereq_and_unlocker_behavior(self):
        prereqs = {
            "CIS 22B": {"prerequisites": ["CIS 22A"], "units": 4.5},
            "CIS 22A": {"prerequisites": [], "units": 4.5},
        }
        expanded = _add_missing_prereqs(
            major_cands=[{"courseCode": "CIS 22B", "units": 4.5}],
            prereqs=prereqs,
            completed=set(),
        )
        codes = {c["courseCode"] for c in expanded}
        self.assertIn("CIS 22A", codes)

        unlockers = _get_unlocker_courses(
            major_cands=[{"courseCode": "CIS 22B", "units": 4.5}],
            completed=set(),
            prereqs=prereqs,
        )
        self.assertTrue(any(u["courseCode"] == "CIS 22A" for u in unlockers))

    def test_warn_and_continue_on_articulation_gap(self):
        # UCX is intentionally missing; planner should warn and continue, not hard-fail.
        result = generate_plan_from_runtime_model(
            college_id="de_anza",
            target_ucs=["UCLA", "UCX"],
            ge_pattern="IGETC",
            completed_courses=[],
            runtime_model=self.runtime.model,
            prereq_records=self.prereqs,
            ge_data=self.ge_data,
            course_reqs_data=self.course_reqs,
        )
        warning_codes = {w.get("code") for w in result.get("warnings", [])}
        self.assertIn("ARTICULATION_GAP", warning_codes)
        self.assertIsInstance(result.get("plan"), list)
        self.assertGreater(len(result["plan"]), 0)


if __name__ == "__main__":
    unittest.main()
