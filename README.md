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

Open:

- `http://127.0.0.1:5173`

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

## Product and Engineering Docs

- `docs/PRD.md`
- `docs/IMPLEMENTATION_PLAN.md`
- `docs/DATA_SPECS.md`
- `docs/DATA_REFRESH_RUNBOOK.md`
- `docs/GOLDEN_WORKFLOW.md`
- `docs/RELIABILITY_SLO.md`
- `docs/PRODUCT_METRICS.md`

## Legacy Notice

The repository previously hosted a research-focused workflow (scraping, district analysis, and research-question notebooks/scripts). That phase is archived under `legacy/` and is not the primary app scope.
