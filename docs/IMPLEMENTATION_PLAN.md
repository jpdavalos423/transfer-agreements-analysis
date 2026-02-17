# Implementation Plan

## Transfer Pathway Planner (PRD-Aligned)

Version: v0.1  
Status: Approved for execution

## 1. Summary
Transform the existing script-based repository into a web app using an incremental, low-risk path:
1. Ship a thin vertical slice first.
2. Build a CSV normalization layer.
3. Gate planner behavior with golden-truth tests on a subset.
4. Expand only after deterministic and NFR compliance.

## 2. Locked Scope and Assumptions
1. Student-first MVP.
2. Source-of-truth inputs: `filtered_results`, `district_csvs`.
3. District mode allows cross-college mixing and assumes equal availability.
4. `Num Required` enforced by distinct row instances.
5. Honors/base equivalence retained globally.
6. GE remains bucket-tracked (IGETC / 7CoursePattern), not concrete GE course suggestion.
7. No mixed quarter/semester conversion logic in MVP.

## 3. Target Architecture
1. `apps/api/`:
   - pathway generation API and metadata endpoints.
2. `apps/web/`:
   - student-facing UI for input, output, warnings.
3. `packages/planner_core/`:
   - extracted planner domain logic, no CLI I/O.
4. `packages/data_adapter/`:
   - CSV parser/validator/normalizer.
5. `packages/shared_types/`:
   - shared request/response/domain schemas.
6. `data/runtime/`:
   - canonical runtime dataset + manifest metadata.
7. `legacy/`:
   - preserved research scripts outside runtime path.
8. `tests/golden/`:
   - scenario definitions, expected outputs, comparator.

## 4. Delivery Phases

## Phase 0: Vertical Slice First
Goal: validate the end-to-end loop before major restructuring.

Tickets:
1. P0-1 Minimal `POST /v1/pathways/generate` endpoint (subset only).
2. P0-2 Minimal web UI (input + term output + warnings).
3. P0-3 Subset data load for De Anza/Lassen and UCLA/UCSD/UCM.
4. P0-4 CI smoke e2e test.

Exit criteria:
1. One full student flow works end-to-end.

## Phase 1: Data Adapter and Runtime Canonicalization
Tickets:
1. P1-1 Implement parser for `filtered_results`.
2. P1-2 Implement parser for `district_csvs`.
3. P1-3 Implement validation severities: `ERROR/WARN/INFO`.
4. P1-4 Build normalized runtime artifacts and manifest checksums/row counts.
5. P1-5 Define data refresh runbook, cadence, and ownership.

Exit criteria:
1. Runtime reads only normalized data artifacts.

## Phase 2: Golden Truth Harness (Phased)
Tickets:
1. P2-1 Build golden runner + semantic comparator + deterministic sort utilities.
2. P2-2 Create scenario schema and fixture loader.
3. P2-3 Add 8 representative golden scenarios (Phase A).
4. P2-4 Add CI gate for Phase A.
5. P2-5 Expand to full 28-scenario golden suite.
6. P2-6 Add reviewed golden update workflow.

Exit criteria:
1. Planner drift is CI-gated.

## Phase 3: Planner Core Migration
Tickets:
1. P3-1 Extract pure planner core from existing scripts.
2. P3-2 Swap JSON articulation dependency for CSV-normalized model.
3. P3-3 Preserve locked semantics:
   - OR-of-AND articulation logic
   - distinct row-instance cardinality
   - honors/base equivalence
   - direct prereq + unlockers
   - warn-and-continue on articulation gaps
4. P3-4 Achieve golden parity in CI.

Exit criteria:
1. CSV-driven planner passes active goldens.

## Phase 4: Backend API Expansion
Tickets:
1. P4-1 `GET /v1/metadata/colleges`
2. P4-2 `GET /v1/metadata/districts`
3. P4-3 `GET /v1/metadata/ucs`
4. P4-4 `GET /v1/health`
5. P4-5 Structured errors and traceable warning payloads.

Exit criteria:
1. Frontend options are fully API-driven.

## Phase 5: Frontend MVP Completion
Tickets:
1. P5-1 Planner setup workflow.
2. P5-2 Results view with deterministic ordering.
3. P5-3 Warnings/unmet panel with confidence labels:
   - Complete with no warnings
   - Complete with caveats
   - Incomplete
4. P5-4 Accessibility/mobile baseline.

Exit criteria:
1. Student can interpret output confidence and gaps clearly.

## Phase 6: NFR and Release Hardening
Tickets:
1. P6-1 Performance tests and p95 latency enforcement.
2. P6-2 Reliability SLI/SLO checks and alerts.
3. P6-3 Determinism repeat-run suite.
4. P6-4 Product metrics instrumentation and dashboards.
5. P6-5 Deployment/runbook/fallback documentation.

Exit criteria:
1. MVP NFR targets are met and monitored.

## 5. Golden Subset Test Plan
1. Colleges: `de_anza`, `lassen`
2. UCs: `UCLA`, `UCSD`, `UCM`
3. UC target sets:
   - `{UCLA}`, `{UCSD}`, `{UCM}`
   - `{UCLA,UCSD}`, `{UCLA,UCM}`, `{UCSD,UCM}`
   - `{UCLA,UCSD,UCM}`
4. GE patterns:
   - `IGETC`
   - `7CoursePattern`
5. Total scenarios: 28
6. Golden source: manually authored expected plans
7. Assertion mode: semantic + stable ordering

## 6. Explicit NFR Targets (MVP)
1. p95 generation latency <= 2.0s on MVP subset.
2. API success rate >= 99.0% for valid requests.
3. Determinism: 100% semantic stability across 10 repeat runs per scenario.
4. Golden CI stability: 0 flaky failures across last 20 main runs.

## 7. Edge-Case Coverage Backlog
1. Duplicate row keys with conflicting alternatives.
2. Course-code formatting anomalies (spacing/casing/punctuation).
3. Multi-course `Receiving` plus repeated-row cardinality handling.
4. District-mode duplicate/equivalent course double-count prevention.
5. GE leftover/subrequirement counting under repeated tags.
6. No-progress termination and user-facing warning quality.

## 8. Scope Guardrails
1. No auth/roles in MVP.
2. No counselor workflow in MVP.
3. No mixed quarter/semester conversion in MVP.
4. No advanced optimization controls in MVP.
5. Defer heavy package split if vertical slice and core migration do not require it.

## 9. MVP Definition of Done
1. Student pathway generation works for subset schools via web UI/API.
2. Planner is CSV-driven from normalized runtime data.
3. Golden suite protects behavior in CI.
4. Functional + edge-case coverage exists for locked semantics.
5. NFR thresholds and product metrics are implemented and observable.
6. Data refresh/deploy runbooks are documented.

