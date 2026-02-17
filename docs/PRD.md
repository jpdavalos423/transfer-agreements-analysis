# Product Requirements Document (PRD)

## Transfer Pathway Planner

Version: v0.1  
Status: Draft (MVP-approved scope)

## 1. Overview
Transfer Pathway Planner is a student-focused web app that generates community-college-to-UC transfer pathways for Computer Science preparation. It uses articulation agreements, prerequisite structures, and GE requirement patterns to produce term-by-term plans and clear warnings when full completion is not possible.

MVP focus is student planning. Counselor workflows are future phases.

## 2. Objectives
1. Help students build realistic transfer pathways for selected UC targets.
2. Increase transparency around articulation gaps and unresolved requirements.
3. Provide deterministic, explainable outputs from the same input/data version.
4. Establish a reliable data and testing foundation for future expansion.

## 3. Target Users
1. Primary (MVP): Community college students planning transfer pathways.
2. Secondary (future): Counselors reviewing/adjusting student plans.

## 4. In Scope (MVP)
1. Pathway generation for selected UC campuses.
2. Two planning modes:
   - College mode (single selected college)
   - District mode (district-wide pool; cross-college mixing allowed)
3. GE pattern support:
   - IGETC
   - 7CoursePattern
4. CSV-based articulation source-of-truth (`filtered_results`, `district_csvs`).
5. Prerequisite-aware planning with direct prereq expansion and unlocker heuristics.
6. Warning-first behavior on incomplete articulation (`Not Articulated`).
7. Term-by-term output with unmet requirement and warning visibility.

## 5. Out of Scope (MVP)
1. Authentication/authorization.
2. Counselor collaboration tools.
3. Advanced optimization controls and objective tuning.
4. Mixed quarter/semester conversion logic in district mode.
5. Concrete GE course recommendation engine (MVP remains GE-bucket based).

## 6. Functional Requirements
1. The system must parse `Courses Group 1..N` as OR-of-AND logic:
   - Across groups: OR
   - Within group (`;`): AND
2. The system must enforce `Num Required` using distinct row-instance semantics.
3. The system must support multi-UC targeting in one plan request.
4. The system must support both IGETC and 7CoursePattern tracking.
5. The system must warn and continue when articulation rows are `Not Articulated`.
6. The system must include prerequisites in planning:
   - immediate eligibility checks
   - direct missing prereq expansion
   - unlocker course heuristics
7. The system must retain global honors/base equivalence behavior.
8. The system must return completion flags and unmet requirements.

## 7. Non-Functional Requirements
1. Determinism:
   - Same input + same dataset version must produce same semantic output and ordering.
2. Performance:
   - p95 generation latency <= 2.0s on MVP subset.
3. Reliability:
   - API success rate >= 99.0% for valid requests.
4. Observability:
   - structured logging, request/run IDs, warning counters, execution timing.

## 8. User Stories
1. As a student, I can choose my college/district, UC targets, and GE pattern, then generate a pathway.
2. As a student, I can see term-by-term selected courses and total progress.
3. As a student, I can see which requirements remain unmet and why.
4. As a student, I can see warnings when required articulation is missing.
5. As a student, I can compare outcomes by changing UC target set or GE pattern.

## 9. Technical Requirements
1. API endpoints:
   - `POST /v1/pathways/generate`
   - `GET /v1/metadata/colleges`
   - `GET /v1/metadata/districts`
   - `GET /v1/metadata/ucs`
   - `GET /v1/health`
2. Data adapter layer from CSV inputs to normalized planner model.
3. Runtime data manifests (checksums, row counts, version metadata).
4. Golden-truth CI suite to gate behavior regressions.

## 10. Success Metrics
1. Pathway completion rate (major + GE + target units).
2. Median terms to completion.
3. Warning incidence rate (`Not Articulated`, blocked progress).
4. Determinism pass rate in repeat-run tests.
5. API failure rate for valid requests.

## 11. Risks and Dependencies
1. CSV quality drift can introduce planning inconsistencies.
2. Row duplication/cardinality edge cases can cause requirement miscounting.
3. District equal-availability assumption may reduce real-world plan realism.
4. Legacy script behavior differences may cause migration drift.
5. Dependencies:
   - articulation CSVs
   - prerequisite JSONs
   - GE and UC requirement definition files

## 12. Initial Golden Subset (MVP Gate)
1. Colleges: De Anza, Lassen
2. UCs: UCLA, UCSD, UCM
3. UC target sets: all non-empty subsets of `{UCLA, UCSD, UCM}`
4. GE patterns: IGETC, 7CoursePattern
5. Total scenarios: 28
6. Golden truth source: manually authored expected plans
7. Assertion mode: semantic + stable ordering

## 13. Roadmap
### MVP
1. Student-first planner flow.
2. CSV adapter + deterministic planner API.
3. Golden CI gate and warning transparency.

### v1 (Future)
1. Enhanced explainability per planning decision.
2. Better data quality dashboards and advisor-ready outputs.
3. Early counselor review mode.

### v2 (Future)
1. Counselor workflows and collaboration tooling.
2. Scenario comparison and richer policy constraints.
3. Expanded optimization controls.

