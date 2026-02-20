# Migration Readiness Checklist

## 1. Purpose

This checklist defines the minimum parity and release gates required to migrate the current stdlib stack (`apps/api`, `apps/web`) to a framework stack (FastAPI + React/Vite) without behavior drift.

Use this document before, during, and immediately before cutover.

## 2. Current Contract Inventory

## 2.1 API endpoints (v1)

These routes and response envelopes are treated as externally stable:

1. `POST /v1/pathways/generate`
2. `GET /v1/metadata/colleges`
3. `GET /v1/metadata/districts`
4. `GET /v1/metadata/ucs`
5. `GET /v1/metadata` (aggregate compatibility route)
6. `GET /v1/health`
7. `GET /v1/metrics`

## 2.2 Request contracts

`POST /v1/pathways/generate` request body fields:

1. `college_id: string`
2. `target_ucs: string[]` (non-empty)
3. `ge_pattern: "IGETC" | "7CoursePattern"`
4. `completed_courses: string[]`

Validation behavior must remain the same:

1. Invalid request returns `400` with standard error envelope.
2. Field-level details are reported in `error.details[]`.

## 2.3 Response contracts

Success envelope (`/v1/pathways/generate`) must include:

1. `version: "v1"`
2. `request_id: string`
3. `plan: term[]`
4. `warnings: warning[]` (normalized shape)
5. `meta: object`

Error envelope must include:

1. `version: "v1"`
2. `request_id: string`
3. `error.code`
4. `error.message`
5. `error.status`
6. `error.path`
7. `error.details[]`

Metadata and health contracts:

1. Metadata endpoints return `{"version":"v1","data":[...]}`.
2. Health returns `version`, `status`, and runtime metadata.
3. Metrics returns deterministic key structure for totals/by_route/product.

Reference source of truth:

1. `packages/shared_types/v1/pathways.py`
2. `apps/api/server.py`

## 2.4 Ordering and determinism rules

The migration must preserve deterministic ordering behavior:

1. API response ordering is not re-sorted by UI.
2. `plan` term order is preserved as returned by API.
3. `courses` order inside each term is preserved as returned by API.
4. Warnings and metadata ordering remains deterministic where currently sorted.
5. All JSON outputs must remain stable across repeat runs for identical inputs.

## 3. Parity Checklist (Must Remain Identical)

Mark each item `PASS` before cutover:

## 3.1 API parity

1. All v1 routes from section 2.1 exist and return matching status codes.
2. Request validation behavior and error codes match (`INVALID_JSON`, `VALIDATION_ERROR`, `NOT_FOUND`, etc.).
3. Response envelope keys/types match shared types exactly.
4. Warning payload normalization (severity/source/trace/details) remains unchanged.
5. Runtime-manifest metadata fields in responses remain unchanged.

## 3.2 Planner behavior parity

1. Golden suite semantic equality passes (Phase A and full suite).
2. Locked semantics remain unchanged:
   - OR-of-AND articulation logic
   - distinct row-instance cardinality
   - honors/base equivalence
   - prereq + unlockers behavior
   - warn-and-continue gaps

## 3.3 Frontend parity

1. Setup page behavior and validation UX are unchanged.
2. `/pathway` page states are unchanged (`idle/loading/success/error`).
3. Structured error rendering and retry behavior are unchanged.
4. Results, warnings, and confidence labels render identically.
5. Same-tab navigation and payload persistence behavior are unchanged.

## 3.4 Ops/observability parity

1. `/v1/health` shape and semantics are unchanged.
2. `/v1/metrics` key layout and value types are unchanged.
3. Reliability/perf scripts still run without new manual steps.

## 4. Required Test Gates Before Cutover

Run all gates on migration branch and again on release candidate commit.

## 4.1 Contract and regression gates

```bash
python3 -m unittest tests/api/test_generate_endpoint.py tests/web/test_ui_smoke.py
```

## 4.2 Golden parity

```bash
scripts/golden --suite phase_a
scripts/golden --suite full
```

## 4.3 Determinism

```bash
scripts/determinism --suite full --repeat 10
```

## 4.4 Reliability SLO gate

```bash
scripts/reliability_check --suite phase_a --repeat 2 --threshold 0.99
```

## 4.5 Performance gate

```bash
scripts/perf --suite phase_a --repeat 3 --warmup 1 --threshold-seconds 2.0
```

## 4.6 Metadata parity spot-check

```bash
curl -s http://127.0.0.1:8000/v1/metadata/colleges
curl -s http://127.0.0.1:8000/v1/metadata/districts
curl -s http://127.0.0.1:8000/v1/metadata/ucs
curl -s http://127.0.0.1:8000/v1/health
curl -s http://127.0.0.1:8000/v1/metrics
```

## 5. Step-by-Step Cutover Readiness Process

1. Confirm runtime artifacts are valid (`data/runtime/manifest.json` present, checksums valid).
2. Run all gates in section 4 on the current stdlib baseline and record results.
3. Run all gates in section 4 on the framework candidate and record results.
4. Compare outputs and metrics for parity deltas.
5. Review parity checklist in section 3 item-by-item.
6. Complete GO/NO-GO decision using section 6.
7. If GO, deploy with rollback window active.
8. Post-deploy, rerun health/metrics/reliability checks.

## 6. GO / NO-GO Criteria

## GO only if ALL are true

1. All required test gates in section 4 pass.
2. No unresolved contract diffs in endpoint payload shapes.
3. No unresolved golden semantic mismatches.
4. Determinism is stable across repeat runs.
5. Performance p95 is within threshold.
6. Reliability SLO gate passes (`>= 99%` for valid requests).
7. Rollback owner and rollback commit target are identified.

## NO-GO if ANY are true

1. Any gate in section 4 fails.
2. Any API contract key/type/status change is unapproved.
3. Golden drift is unexplained or unreviewed.
4. Nondeterminism is observed.
5. Rollback plan cannot be executed immediately.

## 7. Rollback Plan Outline

If migration fails post-cutover:

1. Revert traffic to stdlib stack entrypoint.
2. Revert migration commit(s) or deploy last known-good release.
3. Validate recovery:
   - `GET /v1/health`
   - `POST /v1/pathways/generate` happy-path request
   - reliability check (`scripts/reliability_check ...`)
4. Announce incident + rollback summary.
5. Open follow-up issue with root cause and parity gap.

Reference procedures:

1. `docs/RUNBOOK.md`
2. `docs/DEPLOYMENT.md`
3. `docs/FALLBACKS.md`

## 8. Dependency and Tooling Baseline

Phase 7 baseline adds framework tooling without cutover:

1. Python migration deps in `pyproject.toml` optional group `migration`:
   - `fastapi`
   - `uvicorn[standard]`
   - `ruff`
   - `mypy`
2. JS migration scaffold in `apps/web_react/package.json`:
   - `react`
   - `react-dom`
   - `vite`
   - `typescript`

Install/run commands are documented in `docs/DEV_SETUP.md`.
