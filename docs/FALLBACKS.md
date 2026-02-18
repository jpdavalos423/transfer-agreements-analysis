# Fallback and Degraded Behavior

## 1. Purpose

This document defines current fallback behavior for runtime-data and planner failures.

## 2. Current Fallback Model (MVP)

Current behavior is fail-fast for runtime-data dependencies.

When runtime artifacts are missing/invalid:

1. `GET /v1/health` returns service-unavailable style error (`RUNTIME_METADATA_ERROR`).
2. `GET /v1/metadata/*` returns error (`RUNTIME_METADATA_ERROR`).
3. `POST /v1/pathways/generate` returns error (`RUNTIME_METADATA_ERROR` or `PLANNER_RUNTIME_ERROR`).

There is no hidden partial fallback that fabricates planner output.

## 3. Warning Surfacing Behavior

For successful generate responses:

1. `warnings` is always present as an array.
2. Warning items are normalized with:
   - `code`
   - `message`
   - `severity`
   - `source`
   - `trace_id`
   - `details`

Examples of expected warning conditions:

1. Missing prereq coverage for a college (`PREREQ_GAP`) while still returning a plan.
2. GE pattern issues (`GE_PATTERN_NOT_FOUND`) when applicable.

## 4. Safe-Mode Status

Requested safe mode concept:

1. Read-only metadata remains available while pathway generation is degraded.

Current implementation status:

1. Not implemented.
2. Metadata endpoints currently depend on runtime load and fail when runtime is invalid.

Recommended follow-up ticket:

1. Add cached/embedded metadata fallback for `GET /v1/metadata/colleges`, `GET /v1/metadata/districts`, `GET /v1/metadata/ucs` when runtime artifacts are unavailable.
2. Keep planner generation disabled in degraded mode.

## 5. Operator Actions During Degraded Mode

1. Confirm issue:

```bash
curl -s http://127.0.0.1:8000/v1/health
```

2. Inspect runtime artifacts:

```bash
ls -la data/runtime
cat data/runtime/manifest.json
```

3. Rebuild runtime dataset:

```bash
scripts/build_runtime_dataset
```

4. Re-check health + metrics:

```bash
curl -s http://127.0.0.1:8000/v1/health
curl -s http://127.0.0.1:8000/v1/metrics
```

