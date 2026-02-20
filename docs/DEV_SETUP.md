# Dev Setup (Migration Baseline)

This document defines the dependency/tooling baseline added for Phase 7 ticket P7-11.

The current app remains:

1. API: `apps/api` (stdlib server)
2. Web: `apps/web` (vanilla static UI)

The new framework scaffolds are additive only:

1. `apps/api_fastapi` (FastAPI scaffold)
2. `apps/web_react` (React + Vite scaffold)

## 1. Python Migration Tooling (FastAPI Baseline)

Dependencies are defined in `pyproject.toml` optional group `migration`.

Install (pip):

```bash
python3 -m pip install -e ".[migration]"
```

Run FastAPI scaffold:

```bash
uvicorn apps.api_fastapi.main:app --host 127.0.0.1 --port 8100 --reload
```

Optional tooling commands:

```bash
ruff check apps/api_fastapi
mypy apps/api_fastapi
```

## 2. JS Migration Tooling (React + Vite Baseline)

Scaffold package manifest is in `apps/web_react/package.json`.

Install:

```bash
cd apps/web_react
npm install
```

Run dev server:

```bash
npm run dev
```

Other scripts:

```bash
npm run build
npm run preview
npm run typecheck
```

## 3. Existing App Still Runs (No Cutover)

Current API:

```bash
python3 -m apps.api.server
```

Current web:

```bash
python3 -m apps.web.server
```

Open:

```text
http://127.0.0.1:5173
```
