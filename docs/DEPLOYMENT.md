# Deployment Guide

## 1. Scope

This guide covers how to run the current MVP stack:

1. API: `apps/api`
2. Frontend: `apps/frontend`
3. Runtime data artifacts: `data/runtime`

## 2. Prerequisites

1. Python 3.8+
2. Node.js (only needed for web logic tests)
3. Repository checked out locally

## 3. Runtime Data Requirement

The API requires normalized runtime artifacts:

1. `data/runtime/manifest.json`
2. `data/runtime/filtered_rows.json`
3. `data/runtime/district_rows.json`
4. `data/runtime/filtered_diagnostics.json`
5. `data/runtime/district_diagnostics.json`

If missing/stale, rebuild:

```bash
scripts/build_runtime_dataset
```

Quick verification:

```bash
python3 - <<'PY'
import json
from pathlib import Path
p = Path("data/runtime/manifest.json")
print("exists:", p.exists())
if p.exists():
    m = json.loads(p.read_text(encoding="utf-8"))
    print("version:", m.get("version"))
    print("generated_at:", m.get("generated_at"))
PY
```

## 4. Environment Variables

Optional environment overrides:

1. `TPP_API_HOST` (default: `127.0.0.1`)
2. `TPP_API_PORT` (default: `8000`)
3. `TPP_API_CORS_ENABLED` (default: `true`)
4. `TPP_API_CORS_ALLOWED_ORIGINS` (default: `http://127.0.0.1:3000,http://localhost:3000,http://127.0.0.1:4173,http://localhost:4173,http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:5174,http://localhost:5174`)
5. `TPP_API_LOG_LEVEL` (default: `SILENT`)
6. `TPP_BACKEND_STACK` (default: `fastapi`; values: `fastapi`, `stdlib`)
7. `TPP_FASTAPI_HOST` (default: `127.0.0.1`)
8. `TPP_FASTAPI_PORT` (default: `8100`)
9. `TPP_FRONTEND_HOST` (default: `127.0.0.1`)
10. `TPP_FRONTEND_PORT` (default: `5174`)
11. `VITE_API_BASE_URL` (default: auto-set by `scripts/run_stack`)

Example:

```bash
# API with explicit CORS allowlist:
TPP_API_HOST=0.0.0.0 TPP_API_PORT=9000 TPP_API_CORS_ENABLED=true TPP_API_CORS_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com TPP_API_LOG_LEVEL=INFO python3 -m apps.api.server
```

```bash
VITE_API_BASE_URL=http://127.0.0.1:9000 npm --prefix apps/frontend run dev
```

## 5. Start Services

Single-command launcher (recommended):

```bash
# default mode: frontend + FastAPI backend
TPP_BACKEND_STACK=fastapi scripts/run_stack
```

```bash
# rollback mode: frontend + stdlib backend
TPP_BACKEND_STACK=stdlib scripts/run_stack
```

Rollback is instant: flip `TPP_BACKEND_STACK` back to `stdlib` and restart.

Manual start (equivalent):

Terminal 1 (backend):

```bash
uvicorn apps.backend.main:app --host 127.0.0.1 --port 8100
```

Terminal 2 (frontend):

```bash
cd apps/frontend
npm run dev
```

Open:

1. Frontend: `http://127.0.0.1:5174`
2. FastAPI backend default: `http://127.0.0.1:8100`
3. Stdlib backend (rollback mode): `http://127.0.0.1:8000`

## 5.1 FastAPI Production Serving Profile

Use `scripts/run_backend_prod` for production-like backend startup.

Recommended default for most deployments: `uvicorn` multi-worker profile.

```bash
# default prod profile (uvicorn workers)
scripts/run_backend_prod
```

Gunicorn + Uvicorn workers (if your platform standardizes on gunicorn):

```bash
python3 -m pip install gunicorn
TPP_BACKEND_SERVER=gunicorn scripts/run_backend_prod
```

Key tuning env vars:

1. `TPP_BACKEND_SERVER` (`uvicorn` default, `gunicorn` optional)
2. `TPP_BACKEND_WORKERS` (default: CPU count, minimum 2)
3. `TPP_BACKEND_KEEP_ALIVE_SECONDS` (default: `5`)
4. `TPP_BACKEND_MAX_REQUESTS` (default: `10000`)
5. `TPP_BACKEND_MAX_REQUESTS_JITTER` (default: `500`)
6. `TPP_BACKEND_TIMEOUT_SECONDS` (gunicorn request timeout, default: `30`)
7. `TPP_BACKEND_GRACEFUL_TIMEOUT_SECONDS` (gunicorn graceful timeout, default: `30`)
8. `TPP_BACKEND_UVICORN_GRACEFUL_SHUTDOWN_SECONDS` (uvicorn graceful shutdown timeout, default: `30`)

Rationale:

1. Multiple workers improve throughput and isolate worker crashes.
2. Keep-alive keeps connection reuse efficient without excessive idle retention.
3. `max-requests` + jitter reduces long-running worker drift/memory risk.
4. Timeouts cap hung request impact and support predictable restarts.

Example tuned profile:

```bash
TPP_BACKEND_SERVER=gunicorn \
TPP_BACKEND_WORKERS=4 \
TPP_BACKEND_TIMEOUT_SECONDS=45 \
TPP_BACKEND_GRACEFUL_TIMEOUT_SECONDS=45 \
TPP_BACKEND_KEEP_ALIVE_SECONDS=5 \
TPP_BACKEND_MAX_REQUESTS=12000 \
TPP_BACKEND_MAX_REQUESTS_JITTER=600 \
scripts/run_backend_prod
```

## 6. Post-Start Checks

Health:

```bash
curl -s http://127.0.0.1:8100/v1/health
```

Metadata:

```bash
curl -s http://127.0.0.1:8100/v1/metadata/colleges
curl -s http://127.0.0.1:8100/v1/metadata/ucs
```

Planner request:

```bash
curl -s -X POST http://127.0.0.1:8100/v1/pathways/generate \
  -H "Content-Type: application/json" \
  -d '{"college_id":"de_anza","target_ucs":["UCLA"],"ge_pattern":"IGETC","completed_courses":[]}'
```

Metrics:

```bash
curl -s http://127.0.0.1:8100/v1/metrics
```

Readiness/liveness guidance (`/v1/health`):

1. Liveness probe: HTTP 200 on `/v1/health`.
2. Readiness probe for full planner service: `/v1/health` JSON `status == \"ok\"`.
3. If `/v1/health` returns `status == \"degraded\"`, treat as not-ready for planner generation (safe-mode metadata may still be available).

Mode smoke checks:

```bash
# verify frontend + stdlib backend startup
scripts/smoke_stack_mode --mode stdlib
```

```bash
# verify frontend + fastapi backend startup
scripts/smoke_stack_mode --mode fastapi
```

## 7. CI-Equivalent Validation

```bash
python3 -m compileall -q apps packages tests scripts
python3 -m unittest tests/api/test_generate_endpoint.py
npm --prefix apps/frontend run test:client
npm --prefix apps/frontend run test:ui
scripts/reliability_check --suite phase_a --repeat 2 --threshold 0.99
scripts/perf --suite phase_a --repeat 3 --warmup 1 --threshold-seconds 2.0
scripts/determinism --suite full --repeat 10
```
