# Implementation Plan

## Transfer Pathway Planner (Unified Phases 0-8)

Version: v0.2  
Status: Approved for execution

## 1. Summary
This unified plan combines the existing delivery roadmap with new Phase 7 (Fixes/QOL) and Phase 8 (Framework Migration):
1. Ship and stabilize MVP behavior first.
2. Lock behavior with deterministic golden truth and NFR gates.
3. Clean QOL and migration seams before framework swap.
4. Migrate to FastAPI + React/Vite with parity-first, parallel-run cutover.

## 2. Locked Scope and Assumptions
1. Student-first MVP.
2. Source-of-truth inputs: `filtered_results`, `district_csvs`.
3. District mode allows cross-college mixing and assumes equal availability.
4. `Num Required` enforced by distinct row instances.
5. Honors/base equivalence retained globally.
6. GE remains bucket-tracked (IGETC / 7CoursePattern), not concrete GE course suggestion.
7. No mixed quarter/semester conversion logic in MVP.
8. `/v1` API contracts remain stable through migration.

## 3. Target Architecture
1. `apps/api/`:
   - Current stdlib API transport and handlers.
2. `apps/frontend/`:
   - Current student-facing UI.
3. `packages/planner_core/`:
   - Extracted planner domain logic, no CLI I/O.
4. `packages/data_adapter/`:
   - CSV parser/validator/normalizer.
5. `packages/shared_types/`:
   - Shared request/response/domain schemas.
6. `data/runtime/`:
   - Canonical runtime dataset + manifest metadata.
7. `legacy/`:
   - Preserved research scripts outside runtime path.
8. `tests/golden/`:
   - Scenario definitions, expected outputs, comparator.

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
Goal: normalize source CSVs into deterministic runtime artifacts.

Tickets:
1. P1-1 Implement parser for `filtered_results`.
2. P1-2 Implement parser for `district_csvs`.
3. P1-3 Implement validation severities: `ERROR/WARN/INFO`.
4. P1-4 Build normalized runtime artifacts and manifest checksums/row counts.
5. P1-5 Define data refresh runbook, cadence, and ownership.

Exit criteria:
1. Runtime reads only normalized data artifacts.

## Phase 2: Golden Truth Harness (Phased)
Goal: lock planner behavior and prevent drift.

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
Goal: isolate and preserve planner semantics in pure core.

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
Goal: complete API surface for UI and operations.

Tickets:
1. P4-1 `GET /v1/metadata/colleges`
2. P4-2 `GET /v1/metadata/districts`
3. P4-3 `GET /v1/metadata/ucs`
4. P4-4 `GET /v1/health`
5. P4-5 Structured errors and traceable warning payloads.

Exit criteria:
1. Frontend options are fully API-driven.

## Phase 5: Frontend MVP Completion
Goal: complete student UX for setup/results/confidence.

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
Goal: enforce performance, reliability, determinism, and operability.

Tickets:
1. P6-1 Performance tests and p95 latency enforcement.
2. P6-2 Reliability SLI/SLO checks and alerts.
3. P6-3 Determinism repeat-run suite.
4. P6-4 Product metrics instrumentation and dashboards.
5. P6-5 Deployment/runbook/fallback documentation.

Exit criteria:
1. MVP NFR targets are met and monitored.

## Phase 7: Fixes/QOL and Migration Readiness
Goal: remove MVP debug friction, clean architecture seams, and prepare for framework migration.

Tickets:
1. P7-1 Remove legacy debug response section from web UI.
2. P7-2 Frontend cleanup for migration:
   - Introduce explicit UI state transitions (`idle/loading/success/error`).
   - Centralize API client calls behind a single module.
3. P7-3 API seam extraction:
   - Refactor stdlib transport handlers to call reusable route service functions.
4. P7-4 QOL bugfix pass:
   - Form flow stability, warnings/unmet edge cases, ordering regressions.
5. P7-12 Separate form and pathway pages:
   - Keep setup form on primary page.
   - Navigate in same tab to dedicated `/pathway` page after submit.
   - Pathway page refetches using submitted request payload.
   - Preserve warnings/confidence/results readability and error messaging.
6. P7-5 Migration readiness checklist doc.
7. P7-6 Remove all leftover raw-response plumbing (HTML/CSS/JS/tests/docs).
8. P7-7 Externalize config:
   - Frontend API base URL.
   - Backend host/port/CORS/log-level settings.
9. P7-8 CORS hardening via allowlist (retain local-dev defaults).
10. P7-9 Request lifecycle hygiene:
   - Prevent duplicate in-flight submissions.
   - Stable loading/error transitions.
11. P7-10 Safe-mode metadata fallback:
   - Metadata remains available when runtime planner path is degraded.
   - Pathway generation remains unavailable while degraded.
12. P7-11 Framework dependency/tooling baseline:
   - Python dependency setup for FastAPI/uvicorn.
   - JS dependency setup for React/Vite.

Exit criteria:
1. Student UI is cleaned (no legacy debug response section).
2. Migration seams are explicit and reusable.
3. Safe-mode behavior is defined and implemented.
4. Setup form and pathway output are separated into dedicated pages.

## Phase 8: Framework Migration
Goal: migrate to framework stack with no contract drift and controlled cutover.

Locked migration choices:
1. Backend framework: FastAPI (parity-first).
2. Frontend framework: React + Vite.
3. Cutover strategy: keep old UI in parallel until parity gates pass, then switch default UI/traffic while keeping old backend stack behind a rollback flag.

Tickets:
1. P8-1 Stand up FastAPI app in parallel with route parity.
2. P8-2 Preserve parity for:
   - Structured error envelope
   - Warning payload normalization
   - Metadata/health/metrics shapes
3. P8-3 Stand up React + Vite app in parallel with setup/results/status parity.
4. P8-4 Preserve accessibility/mobile baseline in React app.
5. P8-5 Expand CI for dual-stack checks.
6. P8-6 Cutover switch from stdlib stack to framework stack:
   - Flip DEFAULT traffic/UI to framework stack.
   - Keep old backend stack available behind a rollback flag.
   - Do not delete old UI as part of cutover.
7. P8-7 Add hard old-vs-new contract parity gate:
   - Same scenario requests
   - Semantic comparison on outputs
8. P8-8 Shared typed API client for React (enforced against `shared_types`).
9. P8-9 Observability parity:
   - Keep `/v1/metrics` keys/types/order deterministic.
10. P8-10 Production serving profile:
   - uvicorn/gunicorn worker/timeouts/readiness behavior.
11. P8-11 React resilience:
   - Error boundary/loading boundary/network failure parity.
12. P8-12 Dual-run rollback window and stdlib deprecation plan (merged into P8-13).
13. P8-13 Retire old web app cleanup:
   - Prerequisites:
     - Goldens pass.
     - Determinism suite passes.
     - Perf/reliability gates pass.
     - Manual QA passes.
     - At least one release window (or a few days) with no regressions after default switch.
   - Deliverables:
     - Remove old UI app.
     - Remove old web CI jobs/docs.
     - Update README and run commands.
     - Confirm parity gates remain green after removal.

Exit criteria:
1. Framework stack passes all active golden/NFR/contract tests.
2. Parity checks are green for defined scenario sets.
3. Rollback path is validated before stdlib retirement.
4. Old UI remains in parallel until: goldens, determinism, perf/reliability, and manual QA all pass.
5. At least one release window (or a few days) completes with no regressions before retiring old UI.

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

## 7. Scope Guardrails
1. No auth/roles in MVP.
2. No counselor workflow in MVP.
3. No mixed quarter/semester conversion in MVP.
4. No data contract changes outside versioned process.

## 8. Cross-Phase Validation Gates
1. Golden suites:
   - `scripts/golden --suite phase_a`
   - `scripts/golden --suite full`
2. Determinism:
   - `scripts/determinism --suite full --repeat 10`
3. Reliability:
   - `scripts/reliability_check --suite phase_a --repeat 2 --threshold 0.99`
4. Performance:
   - `scripts/perf --suite phase_a --repeat 3 --warmup 1 --threshold-seconds 2.0`
5. API/frontend regression:
   - `python3 -m unittest tests/api/test_generate_endpoint.py`
   - `npm --prefix apps/frontend run test:client`
   - `npm --prefix apps/frontend run test:ui`

## 9. Unified Definition of Done
1. Student pathway generation works via web UI/API with stable contracts.
2. Planner remains CSV-runtime-driven with locked semantics preserved.
3. Golden + determinism + reliability + performance gates are green.
4. Product metrics and operational docs are complete and current.
5. Framework stack is primary runtime after parity and rollback validation.
