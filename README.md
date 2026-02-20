# Transfer Pathway Planner

Transfer Pathway Planner is a student-facing web application that generates community-college-to-UC Computer Science transfer pathways.

This repository is now application-first (API + React frontend + runtime data pipeline). Prior research artifacts are preserved under `legacy/`.

## Current Scope

- Student planning workflows (MVP)
- API-based pathway generation and metadata endpoints
- Web UI for planner inputs, pathway results, and warnings
- CSV-to-runtime data normalization pipeline
- Deterministic and regression coverage with golden tests

## Repository Structure

| Path | Purpose |
|---|---|
| `apps/api/` | Backend API service (`/v1/pathways/generate`, metadata, health, metrics) |
| `apps/frontend/` | Student-facing React + Vite frontend |
| `packages/planner_core/` | Core planning logic |
| `packages/data_adapter/` | CSV parser/validation/normalization layer |
| `packages/shared_types/` | Shared contracts and schemas |
| `data/runtime/` | Generated runtime artifacts and manifest |
| `tests/` | API, web, data adapter, and golden coverage |
| `docs/` | Product, implementation, data, reliability, and workflow docs |
| `legacy/` | Archived research scripts/results from earlier project phase |

## Run Locally

Requirements:
- Python 3.8+
- Node.js (for frontend)

Start API:

```bash
python3 -m apps.api.server
```

Start frontend app (second terminal):

```bash
npm --prefix apps/frontend install
npm --prefix apps/frontend run dev
```

Or launch frontend + backend with one command:

```bash
TPP_BACKEND_STACK=fastapi scripts/run_stack
TPP_BACKEND_STACK=stdlib scripts/run_stack
```

Open:

- Frontend: `http://127.0.0.1:5174` (or the port Vite prints)

Configurable environment variables (optional):

1. `TPP_API_HOST` (default: `127.0.0.1`)
2. `TPP_API_PORT` (default: `8000`)
3. `TPP_API_CORS_ENABLED` (default: `true`)
4. `TPP_API_CORS_ALLOWED_ORIGINS` (default: `http://127.0.0.1:3000,http://localhost:3000,http://127.0.0.1:4173,http://localhost:4173,http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:5174,http://localhost:5174`)
5. `TPP_API_LOG_LEVEL` (default: `SILENT`)
6. `VITE_API_BASE_URL` (default: auto-set by `scripts/run_stack`)

Example running frontend against a non-default API base URL:

```bash
VITE_API_BASE_URL=http://127.0.0.1:9000 npm --prefix apps/frontend run dev
```

## Data Runtime Refresh

Source-of-truth CSV inputs:
- `filtered_results/`
- `district_csvs/`

Build runtime artifacts:

```bash
scripts/build_runtime_dataset
```

Outputs are written to `data/runtime/`.

Detailed SOP: `docs/DATA_REFRESH_RUNBOOK.md`

## Testing and Reliability

Data adapter tests:

```bash
python3 -m unittest discover -s tests/data_adapter -p 'test_*.py'
```

API smoke:

```bash
python3 -m unittest tests/api/test_generate_endpoint.py
```

Frontend tests:

```bash
npm --prefix apps/frontend run test:client
npm --prefix apps/frontend run test:ui
```

Reliability check:

```bash
scripts/reliability_check --suite phase_a --repeat 2 --threshold 0.99
```

Golden/determinism/perf gates:

```bash
scripts/golden --suite phase_a
scripts/golden --suite full
scripts/determinism --suite full --repeat 10
scripts/perf --suite phase_a --repeat 3 --warmup 1 --threshold-seconds 2.0
```

FastAPI smoke (parallel stack):

```bash
python3 -m pip install fastapi uvicorn
uvicorn apps.backend.main:app --host 127.0.0.1 --port 8100
curl -fsS http://127.0.0.1:8100/v1/health
curl -fsS http://127.0.0.1:8100/v1/metadata/ucs
```

Hard old-vs-new parity gate:

```bash
python3 -m pip install fastapi uvicorn
scripts/parity_gate --suite phase_a
```

Metrics observability parity check:

```bash
python3 -m pip install fastapi uvicorn
python3 -m unittest tests/api_fastapi/test_metrics_observability_parity.py
```

## Product and Engineering Docs

- `docs/PRD.md`
- `docs/IMPLEMENTATION_PLAN.md`
- `docs/DATA_SPECS.md`
- `docs/DATA_REFRESH_RUNBOOK.md`
- `docs/GOLDEN_WORKFLOW.md`
- `docs/RELIABILITY_SLO.md`
- `docs/PRODUCT_METRICS.md`
- `docs/DEPLOYMENT.md`
- `docs/RUNBOOK.md`
- `docs/FALLBACKS.md`
- `docs/MIGRATION_READINESS.md`
- `docs/DEV_SETUP.md`
- `docs/FRONTEND_A11Y_CHECKLIST.md`

## Legacy Notice

The repository previously hosted a research-focused workflow (scraping, district analysis, and research-question notebooks/scripts). That phase is archived under `legacy/` and is not the primary app scope.
