# Deployment Guide

## 1. Scope

This guide covers how to run the current MVP stack:

1. API: `apps/api`
2. Web: `apps/web`
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
4. `TPP_API_CORS_ALLOWED_ORIGINS` (default: `http://127.0.0.1:3000,http://localhost:3000,http://127.0.0.1:4173,http://localhost:4173,http://127.0.0.1:5173,http://localhost:5173`)
5. `TPP_API_LOG_LEVEL` (default: `SILENT`)
6. `TPP_WEB_API_BASE_URL` (default: `http://127.0.0.1:8000`)

Example:

```bash
# API with explicit CORS allowlist:
TPP_API_HOST=0.0.0.0 TPP_API_PORT=9000 TPP_API_CORS_ENABLED=true TPP_API_CORS_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com TPP_API_LOG_LEVEL=INFO python3 -m apps.api.server
```

```bash
TPP_WEB_API_BASE_URL=http://127.0.0.1:9000 python3 -m apps.web.server
```

## 5. Start Services

Terminal 1 (API):

```bash
python3 -m apps.api.server
```

Terminal 2 (web):

```bash
python3 -m apps.web.server
```

Open:

1. `http://127.0.0.1:5173`

## 6. Post-Start Checks

Health:

```bash
curl -s http://127.0.0.1:8000/v1/health
```

Metadata:

```bash
curl -s http://127.0.0.1:8000/v1/metadata/colleges
curl -s http://127.0.0.1:8000/v1/metadata/ucs
```

Planner request:

```bash
curl -s -X POST http://127.0.0.1:8000/v1/pathways/generate \
  -H "Content-Type: application/json" \
  -d '{"college_id":"de_anza","target_ucs":["UCLA"],"ge_pattern":"IGETC","completed_courses":[]}'
```

Metrics:

```bash
curl -s http://127.0.0.1:8000/v1/metrics
```

## 7. CI-Equivalent Validation

```bash
python3 -m compileall -q apps packages tests scripts
python3 -m unittest tests/api/test_generate_endpoint.py tests/web/test_ui_smoke.py
scripts/reliability_check --suite phase_a --repeat 2 --threshold 0.99
scripts/perf --suite phase_a --repeat 3 --warmup 1 --threshold-seconds 2.0
scripts/determinism --suite full --repeat 10
```
