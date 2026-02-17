from __future__ import annotations

import difflib
import json
from typing import Any

from packages.planner_core.sort_utils import canonicalize_for_comparison


def semantic_compare(actual: dict[str, Any], expected: dict[str, Any]) -> tuple[bool, str]:
    """
    Semantic comparison rules:
    1. warning ordering is ignored (sorted by code/message)
    2. target_ucs ordering is ignored (sorted unique values)
    3. plan term ordering is ignored (sorted by normalized term key)
    4. course ordering inside each term is ignored (sorted by courseCode/units)
    5. all compared fields must match logically after canonicalization
    """
    actual_c = canonicalize_for_comparison(actual)
    expected_c = canonicalize_for_comparison(expected)

    if actual_c == expected_c:
        return True, ""

    actual_text = json.dumps(actual_c, sort_keys=True, indent=2).splitlines()
    expected_text = json.dumps(expected_c, sort_keys=True, indent=2).splitlines()
    diff = "\n".join(
        difflib.unified_diff(
            expected_text,
            actual_text,
            fromfile="expected",
            tofile="actual",
            lineterm="",
        )
    )
    return False, diff

