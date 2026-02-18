from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packages.data_adapter.models import ArticulationRow


DEFAULT_MAX_UNITS = 16
DEFAULT_TOTAL_UNITS_REQUIRED = 60
DEFAULT_MAX_TERMS_SAFETY_LIMIT = 9
DEFAULT_ELECTIVE_PADDING_MAX_POOL = 50

COLLEGE_FILTERED_FILES = {
    "de_anza": "De_Anza_College_filtered.csv",
    "lassen": "Lassen_Community_College_filtered.csv",
}
COLLEGE_DISPLAY_NAMES = {
    "de_anza": "De Anza College",
    "lassen": "Lassen Community College",
}
COLLEGE_CC_KEYS = {
    "de_anza": "De_Anza_College",
    "lassen": "Lassen_Community_College",
}


@dataclass(frozen=True)
class PlannerRuntimeModel:
    filtered_rows: tuple[ArticulationRow, ...]
    district_rows: tuple[ArticulationRow, ...]
    manifest: dict[str, Any] | None = None


def _articulation_row_to_dict(row: ArticulationRow) -> dict[str, Any]:
    return {
        "source_file": row.source_file,
        "row_number": row.row_number,
        "mode": row.mode,
        "college_name": row.college_name,
        "uc_name": row.uc_name,
        "group_id": row.group_id,
        "set_id": row.set_id,
        "num_required": row.num_required,
        "receiving_raw": row.receiving_raw,
        "receiving_courses": list(row.receiving_courses),
        "articulation_status": row.articulation_status,
        "alternatives": [
            {
                "block_index": block.block_index,
                "courses": [
                    {
                        "course_code": course.course_code,
                        "units": course.units,
                    }
                    for course in block.courses
                ],
            }
            for block in row.alternatives
        ],
    }


def _warning(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _dedupe_by_code(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for it in items:
        c = it.get("courseCode")
        if not isinstance(c, str):
            continue
        if c in seen:
            continue
        seen.add(c)
        out.append(it)
    return out


def _cc_key(college_id: str) -> str:
    if college_id in COLLEGE_CC_KEYS:
        return COLLEGE_CC_KEYS[college_id]
    return "_".join(part.capitalize() for part in college_id.split("_")) + "_College"


def _filtered_file_for(college_id: str) -> str | None:
    if college_id in COLLEGE_FILTERED_FILES:
        return COLLEGE_FILTERED_FILES[college_id]
    return None


def _college_display_name(college_id: str) -> str | None:
    if college_id in COLLEGE_DISPLAY_NAMES:
        return COLLEGE_DISPLAY_NAMES[college_id]
    return None


def _to_prereq_map(prereq_records: Any) -> dict[str, dict[str, Any]]:
    if isinstance(prereq_records, dict):
        if all(isinstance(v, dict) for v in prereq_records.values()):
            return {str(k): dict(v) for k, v in prereq_records.items()}
        return {}
    if isinstance(prereq_records, list):
        out: dict[str, dict[str, Any]] = {}
        for item in prereq_records:
            if not isinstance(item, dict):
                continue
            code = item.get("courseCode")
            if isinstance(code, str) and code:
                out[code] = dict(item)
        return out
    return {}


def _block_fingerprint(block: list[dict[str, Any]]) -> tuple[tuple[str, float | None], ...]:
    return tuple(
        (str(course.get("course", "")), course.get("units"))
        for course in block
    )


def _select_rows_for_college(
    *,
    college_id: str,
    target_ucs: list[str],
    filtered_rows: list[dict[str, Any]],
    district_rows: list[dict[str, Any]] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    warnings: list[dict[str, str]] = []
    selected: list[dict[str, Any]] = []
    target_uc_set = set(target_ucs)

    expected_filtered_file = _filtered_file_for(college_id)
    expected_college_name = _college_display_name(college_id)

    filtered_matches = []
    for row in filtered_rows:
        if row.get("uc_name") not in target_uc_set:
            continue
        source_name = Path(str(row.get("source_file", ""))).name
        if expected_filtered_file:
            if source_name == expected_filtered_file:
                filtered_matches.append(row)
        else:
            if college_id.replace("_", "").lower() in source_name.replace("_", "").lower():
                filtered_matches.append(row)

    district_matches: list[dict[str, Any]] = []
    for row in district_rows or []:
        if row.get("uc_name") not in target_uc_set:
            continue
        college_name = (row.get("college_name") or "").strip()
        if expected_college_name:
            if college_name == expected_college_name:
                district_matches.append(row)
        else:
            if college_id.replace("_", " ").lower() in college_name.lower():
                district_matches.append(row)

    # Preserve legacy behavior by preferring filtered rows.
    selected = list(filtered_matches)

    if not selected and district_matches:
        selected = list(district_matches)
        warnings.append(
            _warning(
                "USING_DISTRICT_FALLBACK",
                f"No filtered articulation rows found for '{college_id}'. Using district rows.",
            )
        )

    found_ucs = {str(r.get("uc_name")) for r in selected}
    missing_ucs = [uc for uc in target_ucs if uc not in found_ucs]
    if missing_ucs:
        warnings.append(
            _warning(
                "ARTICULATION_GAP",
                f"No articulation rows found for UC target(s): {missing_ucs}.",
            )
        )

    selected_sorted = sorted(
        selected,
        key=lambda r: (
            str(r.get("uc_name", "")),
            str(r.get("group_id", "")),
            str(r.get("set_id", "")),
            str(r.get("receiving_raw", "")),
            int(r.get("row_number") or 0),
            str(r.get("mode", "")),
            str(r.get("source_file", "")),
        ),
    )
    return selected_sorted, warnings


def _group_key(row: dict[str, Any]) -> str:
    group_id = str(row.get("group_id", ""))
    set_id = str(row.get("set_id", ""))
    if set_id and set_id != "A":
        return f"{group_id}_{set_id}"
    return group_id


def _build_articulated_from_rows(
    *,
    college_id: str,
    target_ucs: list[str],
    selected_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    cc_key = _cc_key(college_id)
    out: dict[str, Any] = {cc_key: {}}
    uc_set = set(target_ucs)

    for uc in target_ucs:
        out[cc_key][uc] = {}

    for row in selected_rows:
        uc = str(row.get("uc_name", ""))
        if uc not in uc_set:
            continue
        if str(row.get("articulation_status", "ARTICULATED")) != "ARTICULATED":
            continue

        group_key = _group_key(row)
        receiving_courses = [str(x) for x in row.get("receiving_courses", []) if str(x)]
        course_groups: list[list[dict[str, Any]]] = []
        for alt in row.get("alternatives", []):
            courses = []
            for token in alt.get("courses", []):
                code = token.get("course_code")
                if not code:
                    continue
                courses.append({"course": str(code), "units": token.get("units")})
            if courses:
                course_groups.append(courses)
        if not course_groups:
            continue

        bucket = out[cc_key].setdefault(uc, {})
        entry = bucket.get(group_key)
        if entry is None:
            entry = {
                "set_id": row.get("set_id"),
                "num_required": int(row.get("num_required") or 1),
                "course_groups": [],
            }
            if len(receiving_courses) == 1:
                entry["receiving_course"] = receiving_courses[0]
            else:
                entry["receiving_courses"] = receiving_courses
            bucket[group_key] = entry
        else:
            # Merge receiving courses deterministically if duplicates differ.
            existing_receiving = []
            if "receiving_course" in entry:
                existing_receiving = [entry["receiving_course"]]
            elif "receiving_courses" in entry:
                existing_receiving = list(entry["receiving_courses"])
            merged_receiving = []
            seen_receiving = set()
            for val in existing_receiving + receiving_courses:
                if val not in seen_receiving:
                    seen_receiving.add(val)
                    merged_receiving.append(val)
            if len(merged_receiving) == 1:
                entry.pop("receiving_courses", None)
                entry["receiving_course"] = merged_receiving[0]
            else:
                entry.pop("receiving_course", None)
                entry["receiving_courses"] = merged_receiving

        seen_blocks = {_block_fingerprint(block) for block in entry["course_groups"]}
        for block in course_groups:
            fp = _block_fingerprint(block)
            if fp not in seen_blocks:
                seen_blocks.add(fp)
                entry["course_groups"].append(block)

    return out


def _load_uc_requirement_groups_data(
    course_reqs_data: dict[str, Any],
    selected_ucs: list[str],
) -> dict[str, dict[str, dict[str, Any]]]:
    uc_reqs = course_reqs_data.get("UC_REQUIREMENTS", {})
    groups: dict[str, dict[str, dict[str, Any]]] = {}
    for uc in selected_ucs:
        raw = uc_reqs.get(uc, {})
        if not raw:
            continue
        groups[uc] = {}
        for group_name, options in raw.items():
            if not options:
                continue
            codes = [opt[0] for opt in options]
            num_req = options[0][2] if len(options[0]) >= 3 else len(codes)
            groups[uc][group_name] = {"courses": codes, "num_required": num_req}
    return groups


def _build_uc_block_map_data(
    articulated: dict[str, Any],
    *,
    college_id: str,
    selected_ucs: list[str],
) -> dict[tuple[str, str], list[list[str]]]:
    cc_key = _cc_key(college_id)
    cc_data = articulated.get(cc_key, {})
    block_map: dict[tuple[str, str], list[list[str]]] = {}

    for uc in selected_ucs:
        uc_data = cc_data.get(uc, {})
        for _, entry in uc_data.items():
            recs = []
            if "receiving_course" in entry:
                recs = [entry["receiving_course"]]
            elif "receiving_courses" in entry:
                recs = list(entry["receiving_courses"])
            blocks = [
                [course_obj["course"] for course_obj in group]
                for group in entry.get("course_groups", [])
            ]
            for rec in recs:
                block_map.setdefault((uc, rec), []).extend(blocks)

    return block_map


def _build_uc_group_block_map_data(
    *,
    college_id: str,
    selected_ucs: list[str],
    course_reqs_data: dict[str, Any],
    articulated: dict[str, Any],
) -> tuple[
    dict[tuple[str, str], list[list[str]]],
    dict[str, dict[str, dict[str, Any]]],
]:
    block_map = _build_uc_block_map_data(
        articulated,
        college_id=college_id,
        selected_ucs=selected_ucs,
    )
    group_defs = _load_uc_requirement_groups_data(course_reqs_data, selected_ucs)

    group_block_map: dict[tuple[str, str], list[list[str]]] = {}
    for uc, groups in group_defs.items():
        for grp, meta in groups.items():
            blocks: list[list[str]] = []
            for uccode in meta["courses"]:
                exact_blocks = block_map.get((uc, uccode), [])
                blocks.extend(exact_blocks)

                if not exact_blocks:
                    for (block_uc, block_uccode), block_data in block_map.items():
                        if block_uc != uc:
                            continue
                        if (
                            block_uccode == uccode
                            or block_uccode.startswith(grp)
                            or grp.startswith(block_uccode.split("_")[0])
                        ):
                            blocks.extend(block_data)
            group_block_map[(uc, grp)] = blocks

    return group_block_map, group_defs


@dataclass
class _MajorRequirements:
    group_defs: dict[str, dict[str, dict[str, Any]]]
    group_block_map: dict[tuple[str, str], list[list[str]]]

    def get_remaining_courses(
        self,
        completed: set[str],
        articulated: dict[str, Any],
    ) -> list[dict[str, Any]]:
        remaining: list[dict[str, Any]] = []
        for (uc, group), blocks in self.group_block_map.items():
            uc_group_defs = self.group_defs.get(uc, {})
            if group not in uc_group_defs:
                continue
            num_req = uc_group_defs[group]["num_required"]
            satisfied = sum(
                1
                for block in blocks
                if any(course in completed for course in block)
            )
            if satisfied >= num_req:
                continue

            for block in blocks:
                if not any(course in completed for course in block):
                    for cc_course in block:
                        remaining.append(
                            {
                                "courseCode": cc_course,
                                "units": articulated.get(cc_course, {}).get("units")
                                if isinstance(articulated, dict)
                                else None,
                                "tag": f"{uc}:{group}",
                            }
                        )
                    break
        return remaining


def _get_major_requirements_data(
    *,
    college_id: str,
    selected_ucs: list[str],
    course_reqs_data: dict[str, Any],
    articulated: dict[str, Any],
) -> _MajorRequirements:
    group_block_map, group_defs = _build_uc_group_block_map_data(
        college_id=college_id,
        selected_ucs=selected_ucs,
        course_reqs_data=course_reqs_data,
        articulated=articulated,
    )
    return _MajorRequirements(group_defs=group_defs, group_block_map=group_block_map)


class _GETracker:
    def __init__(self, ge_data: dict[str, Any]):
        self.ge_data = ge_data
        self.ge_patterns: dict[str, list[dict[str, Any]]] = {}
        self.completed_courses: list[dict[str, Any]] = []

    def load_pattern(self, pattern_id: str) -> None:
        pattern = next(
            (p for p in self.ge_data.get("requirementPatterns", []) if p.get("patternId") == pattern_id),
            None,
        )
        if pattern:
            self.ge_patterns[pattern_id] = pattern.get("requirements", [])

    def add_completed_course(self, course_name: str, tags: Any) -> None:
        self.completed_courses.append({"name": course_name, "tags": tags})

    def _evaluate_requirement(self, req: dict[str, Any], completed_courses: list[dict[str, Any]]) -> dict[str, Any] | None:
        req_id = req["reqId"]
        min_courses = req.get("minCourses", 0)
        count = sum(1 for c in completed_courses if req_id in c.get("tags", []))
        remaining_courses = max(0, min_courses - count)
        if remaining_courses == 0:
            return None
        return {"name": req["name"], "courses_remaining": remaining_courses}

    def get_remaining_requirements(self, pattern_id: str) -> dict[str, dict[str, Any]]:
        requirements = self.ge_patterns.get(pattern_id)
        if not requirements:
            return {}

        remaining: dict[str, dict[str, Any]] = {}
        for req in requirements:
            sub_min_total = 0
            if "subRequirements" in req:
                if pattern_id == "7CoursePattern" and req.get("reqId") == "GE_General":
                    sub_ids = [s["reqId"] for s in req["subRequirements"]]
                    sub_maxes = {s["reqId"]: s.get("maxCourses", float("inf")) for s in req["subRequirements"]}
                    taken_per_sub: dict[str, int] = {}
                    for sub_id in sub_ids:
                        count = sum(1 for c in self.completed_courses if sub_id in c.get("tags", []))
                        taken_per_sub[sub_id] = min(count, sub_maxes[sub_id])

                    total_taken = sum(taken_per_sub.values())
                    overall_min = req.get("minCourses", 0)
                    remaining_courses = max(0, overall_min - total_taken)
                    if remaining_courses > 0:
                        remaining[req["reqId"]] = {
                            "name": req["name"],
                            "courses_remaining": remaining_courses,
                        }

                    for sub in req["subRequirements"]:
                        sub_id = sub["reqId"]
                        taken = taken_per_sub.get(sub_id, 0)
                        remaining[sub_id] = {
                            "name": sub["name"] + " (taken)",
                            "courses_remaining": taken,
                        }
                else:
                    leftover_tags: set[str] = set()
                    for sub in req["subRequirements"]:
                        sub_id = sub["reqId"]
                        sub_min = sub.get("minCourses", 0)
                        sub_min_total += sub_min
                        matched = [c for c in self.completed_courses if sub_id in c.get("tags", [])]
                        fulfilled_count = min(len(matched), sub_min)
                        if fulfilled_count < sub_min:
                            remaining[sub_id] = {
                                "name": sub["name"],
                                "courses_remaining": sub_min - fulfilled_count,
                            }
                        leftover_tags.update(c["name"] for c in matched[sub_min:])

                leftover_key = f"{req['reqId']}_Leftover"
                leftover_needed = req.get("minCourses", 0) - sub_min_total
                all_or_tags = {s["reqId"] for s in req["subRequirements"]}
                valid_extra_courses = [
                    c
                    for c in self.completed_courses
                    if any(tag in all_or_tags for tag in c.get("tags", []))
                    and c["name"] in leftover_tags
                ]
                explicit_leftovers = [
                    c for c in self.completed_courses if leftover_key in c.get("tags", [])
                ]
                leftover_remaining = max(
                    0,
                    leftover_needed - len(valid_extra_courses) - len(explicit_leftovers),
                )
                if leftover_remaining > 0:
                    remaining[leftover_key] = {
                        "name": f"{req['name']} (either subcategory)",
                        "courses_remaining": leftover_remaining,
                    }
            else:
                res = self._evaluate_requirement(req, self.completed_courses)
                if res:
                    remaining[req["reqId"]] = res
        return remaining


def _build_ge_lookup_from_data(ge_data: dict[str, Any]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for pattern in ge_data.get("requirementPatterns", []):
        for req in pattern.get("requirements", []):
            if "reqId" in req:
                lookup[req["reqId"]] = req.get("name", req["reqId"])
            for sub in req.get("subRequirements", []):
                if "reqId" in sub:
                    lookup[sub["reqId"]] = sub.get("name", sub["reqId"])
    return lookup


def _build_ge_courses(ge_remaining: dict[str, Any], ge_lookup: dict[str, str], unit_count: int = 3) -> list[dict[str, Any]]:
    ge_courses: list[dict[str, Any]] = []
    for req_id in ge_remaining:
        ge_courses.append(
            {
                "courseCode": req_id,
                "courseName": ge_lookup.get(req_id, req_id),
                "reqIds": [req_id],
                "units": unit_count,
            }
        )
    return ge_courses


def _prereq_block_satisfied(block: Any, completed_courses: set[str]) -> bool:
    if isinstance(block, str):
        return block in completed_courses
    if not block:
        return True
    if isinstance(block, dict) and "and" in block:
        return all(_prereq_block_satisfied(sub, completed_courses) for sub in block["and"])
    if isinstance(block, dict) and "or" in block:
        return any(_prereq_block_satisfied(sub, completed_courses) for sub in block["or"])
    return False


def _course_prereqs_satisfied(course: dict[str, Any], completed_courses: set[str]) -> bool:
    prereqs = course.get("prerequisites")
    if prereqs is None or prereqs == []:
        return True
    if isinstance(prereqs, dict):
        return _prereq_block_satisfied(prereqs, completed_courses)
    if isinstance(prereqs, list):
        if any(isinstance(x, str) and ";" in x for x in prereqs):
            for and_group in prereqs:
                parts = [p.strip() for p in str(and_group).split(";")]
                if not all(part in completed_courses for part in parts):
                    return False
            return True
        return any(str(item) in completed_courses for item in prereqs)
    return True


def _collect_missing_from_block(block: Any, completed: set[str]) -> set[str]:
    missing: set[str] = set()
    if isinstance(block, str):
        return set() if block in completed else {block}
    if not block:
        return set()
    if isinstance(block, dict) and "and" in block:
        for sub in block["and"]:
            missing |= _collect_missing_from_block(sub, completed)
        return missing
    if isinstance(block, dict) and "or" in block:
        if any(_prereq_block_satisfied(opt, completed) for opt in block["or"]):
            return set()
        for opt in block["or"]:
            missing |= _collect_missing_from_block(opt, completed)
        return missing
    if isinstance(block, list):
        if any(isinstance(x, str) and ";" in x for x in block):
            for and_group in block:
                parts = [p.strip() for p in str(and_group).split(";")]
                for part in parts:
                    if part not in completed:
                        missing.add(part)
            return missing
        if any(str(item) in completed for item in block):
            return set()
        return {str(item) for item in block if str(item) not in completed}
    return set()


def _add_missing_prereqs(
    major_cands: list[dict[str, Any]],
    prereqs: dict[str, dict[str, Any]],
    completed: set[str],
    default_units: int = 3,
    dedupe: bool = True,
) -> list[dict[str, Any]]:
    existing = {c.get("courseCode") for c in major_cands}
    i = 0
    while i < len(major_cands):
        code = major_cands[i].get("courseCode")
        raw = prereqs.get(code, {}).get("prerequisites", [])
        if isinstance(raw, dict):
            req_list = raw.get("and", [])
        elif isinstance(raw, list):
            req_list = raw
        else:
            req_list = []

        for entry in req_list:
            if isinstance(entry, dict) and "or" in entry:
                candidates = entry["or"]
            elif isinstance(entry, str):
                candidates = [entry]
            else:
                continue
            for pre in candidates:
                if pre in prereqs and pre not in existing and pre not in completed:
                    units = prereqs[pre].get("units", default_units)
                    major_cands.append({"courseCode": pre, "units": units})
                    existing.add(pre)
        i += 1
    return _dedupe_by_code(major_cands) if dedupe else major_cands


def _course_record(code: str, prereqs: dict[str, dict[str, Any]], default_units: int = 3) -> dict[str, Any]:
    units = None
    if code in prereqs:
        units = prereqs[code].get("units") or prereqs[code].get("courseUnits")
    return {"courseCode": code, "units": units if units is not None else default_units}


def _get_eligible_courses(
    completed_courses: set[str],
    major_cands: list[dict[str, Any]],
    prereqs: dict[str, dict[str, Any]],
    default_units: int = 3,
) -> list[dict[str, Any]]:
    eligible: list[dict[str, Any]] = []
    for cand in major_cands:
        code = cand.get("courseCode")
        raw_pr = prereqs.get(code, {}).get("prerequisites", None)
        if code in completed_courses:
            continue
        if _course_prereqs_satisfied({"prerequisites": raw_pr}, completed_courses):
            eligible.append(_course_record(code, prereqs, default_units))
    return _dedupe_by_code(eligible)


def _get_unlocker_courses(
    major_cands: list[dict[str, Any]],
    completed: set[str],
    prereqs: dict[str, dict[str, Any]],
    *,
    min_unlocks: int = 1,
    max_count: int = 6,
    default_units: int = 3,
) -> list[dict[str, Any]]:
    blocked: list[tuple[str, Any]] = []
    for cand in major_cands:
        code = cand.get("courseCode")
        raw = prereqs.get(code, {}).get("prerequisites")
        if code in completed:
            continue
        if not _course_prereqs_satisfied({"prerequisites": raw}, completed):
            blocked.append((code, raw))

    unlock_count: dict[str, int] = {}
    unlock_targets: dict[str, set[str]] = {}
    for blk_code, blk_raw in blocked:
        missing = _collect_missing_from_block(blk_raw, completed)
        for pre in missing:
            if pre not in prereqs:
                continue
            if not _course_prereqs_satisfied(prereqs[pre], completed):
                continue
            unlock_count[pre] = unlock_count.get(pre, 0) + 1
            unlock_targets.setdefault(pre, set()).add(blk_code)

    ranked = sorted(
        ((code, cnt) for code, cnt in unlock_count.items() if cnt >= min_unlocks),
        key=lambda t: (-t[1], t[0]),
    )

    out: list[dict[str, Any]] = []
    for code, cnt in ranked[:max_count]:
        rec = _course_record(code, prereqs, default_units)
        rec.update(
            {
                "tag": "UNLOCKER",
                "unlocks": sorted(unlock_targets.get(code, set())),
                "unlockCount": cnt,
            }
        )
        out.append(rec)
    return _dedupe_by_code(out)


def _select_courses_for_term(
    candidates: list[dict[str, Any]],
    completed: set[str],
    uc_to_cc_map: dict[str, list[list[str]]],
    all_cc_course_codes: set[str],
    max_units: int,
) -> tuple[list[dict[str, Any]], float, set[str]]:
    remaining_ges = [c for c in candidates if "reqIds" in c]
    remaining_majors = [c for c in candidates if "reqIds" not in c]
    selected: list[dict[str, Any]] = []
    total_units: float = 0.0
    pruned_codes: set[str] = set()

    if remaining_ges:
        ge = remaining_ges.pop(0)
        ge_units = float(ge.get("units") or 0)
        if total_units + ge_units <= max_units:
            selected.append(ge)
            total_units += ge_units
            completed.add(ge["courseCode"])

    for major in remaining_majors:
        code = major["courseCode"]
        units = float(major.get("units") or 0)
        if code in completed:
            continue
        if total_units + units > max_units:
            continue
        selected.append(major)
        total_units += units
        completed.add(code)

        base = code.rstrip("H")
        hon = base + "H"
        for eq in (base, hon):
            if eq != code and eq in all_cc_course_codes:
                completed.add(eq)

        for uc_course, blocks in list(uc_to_cc_map.items()):
            if any(set(block).issubset(completed) for block in blocks):
                del uc_to_cc_map[uc_course]
                for block in blocks:
                    for cc_code in block:
                        if cc_code not in completed:
                            pruned_codes.add(cc_code)
                break

    for ge in remaining_ges:
        code = ge["courseCode"]
        units = float(ge.get("units") or 0)
        if code in completed:
            continue
        if total_units + units <= max_units:
            selected.append(ge)
            total_units += units
            completed.add(code)

    return selected, total_units, pruned_codes


def _get_course_units(course_code: str, prereqs: dict[str, dict[str, Any]], articulated: dict[str, Any]) -> float:
    code_raw = course_code
    code_norm = str(course_code).strip() if course_code is not None else course_code

    if isinstance(code_norm, str) and code_norm in prereqs and code_norm != code_raw:
        course_data = prereqs[code_norm]
        if isinstance(course_data, dict):
            if "units" in course_data and course_data["units"] is not None:
                return float(course_data["units"])
            if "courseUnits" in course_data and course_data["courseUnits"] is not None:
                return float(course_data["courseUnits"])

    if code_raw in prereqs:
        course_data = prereqs[code_raw]
        if isinstance(course_data, dict):
            if "units" in course_data and course_data["units"] is not None:
                return float(course_data["units"])
            if "courseUnits" in course_data and course_data["courseUnits"] is not None:
                return float(course_data["courseUnits"])

    for cc_data in articulated.values():
        if not isinstance(cc_data, dict):
            continue
        for uc_data in cc_data.values():
            if not isinstance(uc_data, dict):
                continue
            for req_data in uc_data.values():
                if not isinstance(req_data, dict):
                    continue
                for course_group in req_data.get("course_groups", []):
                    for course in course_group:
                        if course.get("course") == course_code:
                            if "units" in course and course["units"] is not None:
                                return float(course["units"])
                            if "courseUnits" in course and course["courseUnits"] is not None:
                                return float(course["courseUnits"])

    return 3.0


def _ensure_course_has_units(
    course_dict: dict[str, Any],
    prereqs: dict[str, dict[str, Any]],
    articulated: dict[str, Any],
) -> dict[str, Any]:
    code = course_dict.get("courseCode")
    if not code:
        return course_dict
    if "units" in course_dict and course_dict["units"] is not None:
        return course_dict
    course_dict["units"] = _get_course_units(code, prereqs, articulated)
    return course_dict


def _is_major_requirement_complete(
    major_reqs: _MajorRequirements,
    completed: set[str],
    articulated: dict[str, Any],
) -> bool:
    remaining = major_reqs.get_remaining_courses(completed, articulated)
    return len(remaining) == 0


def _can_make_progress(
    eligible_major: list[dict[str, Any]],
    eligible_ge: list[dict[str, Any]],
    completed_before_term: set[str],
) -> bool:
    eligible_major_codes = {c.get("courseCode") for c in eligible_major}
    eligible_ge_codes = {c.get("courseCode") for c in eligible_ge}
    all_eligible = eligible_major_codes.union(eligible_ge_codes)
    return len(all_eligible - completed_before_term) > 0


def _infer_ge_key(course: dict[str, Any]) -> str | None:
    ge_key = course.get("geKey")
    if isinstance(ge_key, str) and ge_key:
        return ge_key.split("__")[0]
    req_ids = course.get("reqIds")
    if isinstance(req_ids, list) and req_ids:
        if isinstance(req_ids[0], str):
            return req_ids[0].split("__")[0]
    code = course.get("courseCode")
    if isinstance(code, str) and code.startswith("IG_"):
        return code.split("__")[0]
    return None


def _expand_ge_into_slots(
    ge_remaining: dict[str, Any],
    ge_course_dicts: list[dict[str, Any]],
    prereqs: dict[str, dict[str, Any]],
    articulated: dict[str, Any],
    completed: set[str],
) -> list[dict[str, Any]]:
    base_templates = {c.get("courseCode"): c for c in ge_course_dicts if isinstance(c, dict)}
    expanded: list[dict[str, Any]] = []

    for ge_key, info in (ge_remaining or {}).items():
        need = int((info or {}).get("courses_remaining", 0) or 0)
        if need <= 0:
            continue

        base_template = base_templates.get(ge_key)
        if not base_template:
            base_template = {"courseCode": ge_key, "units": 3, "reqIds": [ge_key], "geKey": ge_key}
        else:
            base_template = _ensure_course_has_units(dict(base_template), prereqs, articulated)
            if "geKey" not in base_template:
                base_template["geKey"] = ge_key
            if "reqIds" not in base_template:
                base_template["reqIds"] = [ge_key]

        base_in_completed = ge_key in completed
        if base_in_completed:
            for i in range(1, need + 1):
                expanded.append(
                    {
                        "courseCode": f"{ge_key}__slot{i}",
                        "units": base_template.get("units", 3),
                        "reqIds": [ge_key],
                        "geKey": ge_key,
                    }
                )
        else:
            expanded.append(base_template)
            for i in range(1, max(need - 1, 0) + 1):
                expanded.append(
                    {
                        "courseCode": f"{ge_key}__slot{i}",
                        "units": base_template.get("units", 3),
                        "reqIds": [ge_key],
                        "geKey": ge_key,
                    }
                )
    return expanded


def _export_term_plan(term_name: str, selected_courses: list[dict[str, Any]], output_plan: list[dict[str, Any]]) -> None:
    term_entry = {"term": term_name, "courses": []}
    for course in selected_courses:
        course_entry: dict[str, Any] = {
            "courseCode": course.get("courseCode"),
            "units": course.get("units", 0),
        }
        if "tags" in course:
            course_entry["tags"] = course["tags"]
        if "fulfills" in course:
            course_entry["fulfills"] = course["fulfills"]
        term_entry["courses"].append(course_entry)
    output_plan.append(term_entry)


def _major_map_from_articulated(
    articulated: dict[str, Any],
    *,
    college_id: str,
    selected_ucs: list[str],
) -> dict[str, dict[str, list[list[str]]]]:
    cc_key = _cc_key(college_id)
    cc_data = articulated.get(cc_key, {})
    uc_to_map: dict[str, dict[str, list[list[str]]]] = {}
    for uc in selected_ucs:
        uc_entries = cc_data.get(uc, {})
        uc_map: dict[str, list[list[str]]] = {}
        for _, req_obj in uc_entries.items():
            recs = []
            if "receiving_course" in req_obj:
                recs = [req_obj["receiving_course"]]
            elif "receiving_courses" in req_obj:
                recs = req_obj["receiving_courses"]
            blocks = [
                [course_obj["course"] for course_obj in group]
                for group in req_obj.get("course_groups", [])
            ]
            for rec in recs:
                uc_map.setdefault(rec, []).extend(blocks)
        uc_to_map[uc] = uc_map
    return uc_to_map


def generate_plan_from_runtime_model(
    *,
    college_id: str,
    target_ucs: list[str],
    ge_pattern: str,
    completed_courses: list[str],
    runtime_model: PlannerRuntimeModel,
    prereq_records: Any,
    ge_data: dict[str, Any],
    course_reqs_data: dict[str, Any],
    max_units_per_term: int = DEFAULT_MAX_UNITS,
    total_units_required: int = DEFAULT_TOTAL_UNITS_REQUIRED,
    max_terms_safety_limit: int = DEFAULT_MAX_TERMS_SAFETY_LIMIT,
    elective_padding_max_pool: int = DEFAULT_ELECTIVE_PADDING_MAX_POOL,
) -> dict[str, Any]:
    filtered_rows = [_articulation_row_to_dict(r) for r in runtime_model.filtered_rows]
    district_rows = [_articulation_row_to_dict(r) for r in runtime_model.district_rows]
    result = generate_plan_from_runtime(
        college_id=college_id,
        target_ucs=target_ucs,
        ge_pattern=ge_pattern,
        completed_courses=completed_courses,
        filtered_rows=filtered_rows,
        district_rows=district_rows,
        prereq_records=prereq_records,
        ge_data=ge_data,
        course_reqs_data=course_reqs_data,
        max_units_per_term=max_units_per_term,
        total_units_required=total_units_required,
        max_terms_safety_limit=max_terms_safety_limit,
        elective_padding_max_pool=elective_padding_max_pool,
    )
    if runtime_model.manifest:
        result.setdefault("meta", {})
        result["meta"]["runtime_manifest_version"] = runtime_model.manifest.get("version")
    return result


def generate_plan_from_runtime(
    *,
    college_id: str,
    target_ucs: list[str],
    ge_pattern: str,
    completed_courses: list[str],
    filtered_rows: list[dict[str, Any]],
    district_rows: list[dict[str, Any]] | None,
    prereq_records: Any,
    ge_data: dict[str, Any],
    course_reqs_data: dict[str, Any],
    max_units_per_term: int = DEFAULT_MAX_UNITS,
    total_units_required: int = DEFAULT_TOTAL_UNITS_REQUIRED,
    max_terms_safety_limit: int = DEFAULT_MAX_TERMS_SAFETY_LIMIT,
    elective_padding_max_pool: int = DEFAULT_ELECTIVE_PADDING_MAX_POOL,
) -> dict[str, Any]:
    warnings: list[dict[str, str]] = []

    selected_rows, row_warnings = _select_rows_for_college(
        college_id=college_id,
        target_ucs=target_ucs,
        filtered_rows=filtered_rows,
        district_rows=district_rows,
    )
    warnings.extend(row_warnings)
    articulated = _build_articulated_from_rows(
        college_id=college_id,
        target_ucs=target_ucs,
        selected_rows=selected_rows,
    )

    prereqs = _to_prereq_map(prereq_records)
    if not prereqs:
        warnings.append(
            _warning(
                "PREREQ_GAP",
                f"No prerequisite records available for '{college_id}'. Default units/fallback behavior may be used.",
            )
        )

    ge_tracker = _GETracker(ge_data)
    ge_tracker.load_pattern(ge_pattern)
    if ge_pattern not in ge_tracker.ge_patterns:
        warnings.append(
            _warning(
                "GE_PATTERN_NOT_FOUND",
                f"GE pattern '{ge_pattern}' not found in provided GE data.",
            )
        )

    major_reqs = _get_major_requirements_data(
        college_id=college_id,
        selected_ucs=target_ucs,
        course_reqs_data=course_reqs_data,
        articulated=articulated,
    )
    ge_lookup = _build_ge_lookup_from_data(ge_data)

    major_map = _major_map_from_articulated(
        articulated,
        college_id=college_id,
        selected_ucs=target_ucs,
    )
    uc_to_cc_map: dict[str, list[list[str]]] = {}
    for _, cmap in major_map.items():
        for uc_course, blocks in cmap.items():
            uc_to_cc_map.setdefault(uc_course, []).extend(blocks)

    all_cc_course_codes = set(prereqs.keys())
    completed = set(completed_courses or [])
    total_units = 0.0
    term_num = 1
    pathway: list[dict[str, Any]] = []

    while True:
        completed_before_term = completed.copy()

        major_cands = major_reqs.get_remaining_courses(completed, articulated)
        major_cands = _add_missing_prereqs(major_cands, prereqs, completed)
        major_cands = [_ensure_course_has_units(course, prereqs, articulated) for course in major_cands]

        major_done = _is_major_requirement_complete(major_reqs, completed, articulated)
        ge_remaining = ge_tracker.get_remaining_requirements(ge_pattern)

        base_ge_courses = _build_ge_courses(ge_remaining, ge_lookup, unit_count=3)
        base_ge_courses = [_ensure_course_has_units(course, prereqs, articulated) for course in base_ge_courses]
        ge_course_dicts = _expand_ge_into_slots(ge_remaining, base_ge_courses, prereqs, articulated, completed)

        ge_done = not ge_remaining
        min_units_met = total_units >= total_units_required
        if major_done and ge_done and min_units_met:
            break

        eligible_major = _get_eligible_courses(completed, major_cands, prereqs)
        blocked_major = [
            c
            for c in major_cands
            if (c["courseCode"] if isinstance(c, dict) else c)
            not in {e["courseCode"] for e in eligible_major}
        ]
        blocked_major = [
            c
            if isinstance(c, dict)
            else {"courseCode": c, "units": prereqs.get(c, {}).get("units", 3)}
            for c in blocked_major
        ]
        unlockers = _get_unlocker_courses(blocked_major, completed, prereqs)
        merged_major_pool = _dedupe_by_code(unlockers + eligible_major)

        available_ge_courses = [course for course in ge_course_dicts if course.get("courseCode") not in completed]

        if major_done and ge_done and not min_units_met:
            padding: list[dict[str, Any]] = []
            counter = 0
            for code in sorted(all_cc_course_codes):
                if counter >= elective_padding_max_pool:
                    break
                if code in completed:
                    continue
                if code.startswith("IG_"):
                    continue
                if " " not in code and not any(
                    code.startswith(prefix)
                    for prefix in ["CS", "MATH", "PHYS", "CHEM", "BIO", "ENGL", "HIST", "PHIL", "ECON", "PSY", "SOC"]
                ):
                    continue
                units = _get_course_units(code, prereqs, articulated)
                if not units:
                    continue
                padding.append({"courseCode": code, "units": units, "tag": "ELECTIVE"})
                counter += 1
            if padding:
                available_ge_courses = available_ge_courses + padding

        if not _can_make_progress(merged_major_pool, available_ge_courses, completed_before_term):
            warnings.append(
                _warning(
                    "NO_PROGRESS",
                    "No new eligible courses available; ending pathway generation early.",
                )
            )
            break

        eligible_course_dicts = []
        for e in merged_major_pool:
            code = e["courseCode"]
            actual_units = _get_course_units(code, prereqs, articulated)
            course_dict = {"courseCode": code, "units": actual_units}
            for key, value in e.items():
                if key not in course_dict and key != "units":
                    course_dict[key] = value
            eligible_course_dicts.append(course_dict)

        total_eligible = eligible_course_dicts + available_ge_courses
        if not total_eligible:
            warnings.append(
                _warning(
                    "NO_ELIGIBLE_COURSES",
                    "No eligible courses available this term; ending pathway generation.",
                )
            )
            break

        selected, units, _ = _select_courses_for_term(
            total_eligible,
            completed,
            uc_to_cc_map,
            all_cc_course_codes,
            max_units_per_term,
        )
        if not selected:
            warnings.append(
                _warning(
                    "BALANCER_EMPTY_SELECTION",
                    "Unit balancer returned no courses; ending pathway generation.",
                )
            )
            break

        for i, course in enumerate(selected):
            course_code = course["courseCode"]
            if "units" not in course or course["units"] is None:
                course["units"] = _get_course_units(course_code, prereqs, articulated)
            selected[i] = course

        for course in selected:
            code = course["courseCode"]
            completed.add(code)
            ge_key = _infer_ge_key(course)
            if ge_key is not None:
                ge_tracker.add_completed_course(code, ge_key)
            else:
                credited = course.get("tag", code)
                ge_tracker.add_completed_course(code, credited)

        _export_term_plan(f"Term {term_num}", selected, pathway)
        total_units += units
        term_num += 1

        if term_num > max_terms_safety_limit:
            warnings.append(
                _warning(
                    "MAX_TERMS_REACHED",
                    f"Reached max term safety limit ({max_terms_safety_limit}).",
                )
            )
            break
        if completed == completed_before_term:
            warnings.append(
                _warning(
                    "NO_TERM_PROGRESS",
                    "No newly completed courses this term; ending pathway generation.",
                )
            )
            break

    return {
        "plan": pathway,
        "warnings": warnings,
        "meta": {
            "college_id": college_id,
            "target_ucs": list(target_ucs),
            "ge_pattern": ge_pattern,
            "completed_courses_count": len(completed_courses or []),
            "final_total_units": total_units,
            "generated_terms": len(pathway),
        },
    }
