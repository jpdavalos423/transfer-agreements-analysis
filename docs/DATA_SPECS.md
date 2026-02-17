# Data Specs: Transfer Pathway Planner

Version: v0.1  
Status: Draft (MVP-aligned)

## 1. Purpose
Define canonical data inputs, normalization rules, validation behavior, and runtime contracts for pathway generation.

## 2. Scope
Included:
1. `filtered_results/*.csv` (college-level articulations)
2. `district_csvs/*.csv` (district-level articulations)
3. `prerequisites/*.json` (course metadata + prereqs)
4. `prerequisites/ge_reqs.json` (GE patterns)
5. `scraping/files/course_reqs.json` (UC requirement groups)

Excluded:
1. Scraping implementation details
2. Counselor-specific models
3. Mixed quarter/semester conversion logic

## 3. Source-of-Truth Hierarchy
1. Articulation truth: `filtered_results` and `district_csvs`
2. Requirement definitions: `course_reqs.json` and `ge_reqs.json`
3. Course prerequisites/units: `prerequisites/*_prereqs.json`

## 4. Articulation CSV Contract

### 4.1 Required Columns
College-level:
1. `UC Name`
2. `Group ID`
3. `Set ID`
4. `Num Required`
5. `Receiving`
6. `Courses Group 1`
7. `Courses Group 2..N` (optional)

District-level:
1. all above
2. `College Name` (required)

### 4.2 Logical Semantics
For each row:
1. `Courses Group 1..N` are OR alternatives.
2. Within each populated group cell, semicolon-separated courses are AND requirements.

Formal:
1. `Row = Group1 OR Group2 OR ... OR GroupN`
2. `GroupK = CourseA [; CourseB ; ...]`

### 4.3 Unarticulated Sentinel
1. `Courses Group 1 = "Not Articulated"` indicates no valid articulation.
2. Planner behavior: warn and continue.

## 5. Canonical Normalized Models

### 5.1 ArticulationRowNormalized
1. `source_file: string`
2. `source_row: int`
3. `mode: "college" | "district"`
4. `college_name?: string`
5. `uc_name: string`
6. `group_id: string`
7. `set_id: string`
8. `num_required: int`
9. `receiving_raw: string`
10. `receiving_courses: string[]`
11. `alternatives: AlternativeBlock[]`
12. `articulation_status: "ARTICULATED" | "NOT_ARTICULATED"`

### 5.2 AlternativeBlock
1. `block_index: int`
2. `logic: "AND"`
3. `courses: CourseToken[]`

### 5.3 CourseToken
1. `course_code: string`
2. `units: number | null`

## 6. Parsing Rules
1. Parse `Num Required` as integer.
2. Parse `Receiving` by `;` into `receiving_courses`.
3. Process populated `Courses Group k` columns in numeric order.
4. Split each group by `;` into AND courses.
5. Parse token form `<course_code> (<units>)`.
6. If units missing, set `units = null` and emit warning.
7. Preserve row-instance identity; do not silently dedupe.

## 7. Cardinality and Satisfaction
1. `Num Required > 1` is enforced through distinct row instances.
2. Repeated rows are separate required slots unless explicitly re-mapped by policy.
3. Group satisfaction is evaluated per row, then aggregated by requirement cardinality.

## 8. GE Data Contract
1. Supported patterns:
   - `IGETC`
   - `7CoursePattern`
2. GE in MVP is bucket-based, not concrete course recommendation.
3. Planner tracks requirement completion by course counts per GE pattern.
4. `minUnits` fields are informational unless separately enforced.

## 9. Prerequisite Data Contract
Supported structures:
1. `[]` or `null`
2. list of strings
3. dict blocks with `and` / `or`
4. legacy list entries with `;` interpreted as AND groups

MVP planning behavior:
1. immediate eligibility checks
2. direct missing-prereq expansion
3. unlocker heuristic for blocked major requirements

## 10. Honors Equivalence Policy
1. Global base/honors equivalence remains enabled.
2. Completing one variant can mark the counterpart completed when present.

## 11. Validation Model

### 11.1 ERROR (block run)
1. Missing required columns
2. Non-parseable required `Num Required`
3. No usable `Courses Group` data and not marked `Not Articulated`
4. Invalid row shape

### 11.2 WARN (continue run)
1. Missing units in course token
2. Duplicate near-identical rows
3. Inconsistent course formatting
4. `Not Articulated` requirement rows
5. Potential cardinality mismatch

### 11.3 INFO
1. Dataset/file statistics
2. Parsed alternative counts
3. Coverage summary

## 12. Runtime Data Layout
1. `data/runtime/filtered_results/`
2. `data/runtime/district_csvs/`
3. `data/runtime/manifests/dataset_manifest.json`

Minimum manifest fields:
1. `dataset_version`
2. `generated_at`
3. `files[]` with checksum and row_count
4. `source_paths`

## 13. API Data Contracts

### 13.1 PathwayRequest
1. `mode: "college" | "district"`
2. `college_id?: string`
3. `district_id?: string`
4. `selected_ucs: string[]`
5. `ge_pattern: "IGETC" | "7CoursePattern"`

### 13.2 PathwayResponse
1. `run_id: string`
2. `dataset_version: string`
3. `terms: TermPlan[]`
4. `total_units: number`
5. `completion_flags`
6. `warnings: Warning[]`
7. `unmet_requirements: UnmetRequirement[]`

## 14. Golden Truth Initial Scope
1. Colleges: De Anza, Lassen
2. UCs: UCLA, UCSD, UCM
3. UC sets: all non-empty subsets of `{UCLA, UCSD, UCM}`
4. GE patterns: IGETC and 7CoursePattern
5. Total scenarios: 28

## 15. Determinism Requirements
1. Stable ordering for alternatives, selected courses, warnings, unmet requirements.
2. Same request + same dataset version must produce equivalent semantic output.

## 16. Known Constraints
1. District mode assumes equal course availability.
2. No mixed quarter/semester conversion in MVP.
3. Counselor-specific data models are out of scope in MVP.

## 17. Change Control
1. Contract-breaking schema changes require version bump.
2. Golden fixtures must be intentionally updated and reviewed.
3. Runtime manifest version must change whenever canonical data changes.

