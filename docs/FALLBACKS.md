# Fallback and Degraded Behavior

## 1. Purpose

This document defines current fallback behavior for runtime-data and planner failures.

## 2. Current Fallback Model (MVP)

Safe mode is implemented for degraded runtime-data conditions.

When runtime artifacts are missing/invalid:

1. `GET /v1/metadata/colleges` returns `200` with structured metadata (best-effort from source file inventory).
2. `GET /v1/metadata/districts` returns `200` with structured metadata (best-effort from source file inventory).
3. `GET /v1/metadata/ucs` returns `200` with structured metadata (may be empty if runtime-derived UC data is unavailable).
4. `POST /v1/pathways/generate` returns `503` with structured error code `PLANNER_UNAVAILABLE_DEGRADED`.
5. `GET /v1/health` returns `200` with `status: \"degraded\"` and `runtime.safe_mode: true`.

Safe mode does not fabricate planner output.

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

Implemented behavior:

1. Read-only metadata stays available during degraded runtime conditions.
2. Planner generation is disabled while degraded.
3. Health explicitly signals degraded mode.

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
