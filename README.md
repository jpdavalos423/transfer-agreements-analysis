# Transfer Pathway Planner

Transfer Pathway Planner is a student-facing web application that generates community-college-to-UC Computer Science transfer pathways.

This repository is now application-first (API + web + runtime data pipeline). Prior research artifacts are preserved under `legacy/`.

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
| `apps/web/` | Student-facing frontend |
| `apps/frontend/` | Parallel React + Vite frontend (Phase 8 migration track) |
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
- Node.js (for web logic tests)

Start API:

```bash
python3 -m apps.api.server
```

Start web app (second terminal):

```bash
python3 -m apps.web.server
```

Start React + Vite app (optional parallel frontend):

```bash
cd apps/frontend
npm install
npm run dev
```

Open:

- Existing web: `http://127.0.0.1:5173`
- React + Vite web: `http://127.0.0.1:5174` (or the port Vite prints)

Configurable environment variables (optional):

1. `TPP_API_HOST` (default: `127.0.0.1`)
2. `TPP_API_PORT` (default: `8000`)
3. `TPP_API_CORS_ENABLED` (default: `true`)
4. `TPP_API_CORS_ALLOWED_ORIGINS` (default: `http://127.0.0.1:3000,http://localhost:3000,http://127.0.0.1:4173,http://localhost:4173,http://127.0.0.1:5173,http://localhost:5173`)
5. `TPP_API_LOG_LEVEL` (default: `SILENT`)
6. `TPP_WEB_API_BASE_URL` (default: `http://127.0.0.1:8000`)

Example running web against a non-default API base URL:

```bash
TPP_WEB_API_BASE_URL=http://127.0.0.1:9000 python3 -m apps.web.server
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

API + web smoke:

```bash
python3 -m unittest tests/api/test_generate_endpoint.py tests/web/test_ui_smoke.py
```

Web logic tests:

```bash
node --test tests/web/test_planner_form_logic.mjs tests/web/test_results_view_logic.mjs tests/web/test_status_panel_logic.mjs
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
