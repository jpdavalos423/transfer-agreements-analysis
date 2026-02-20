# Dev Setup (Migration Baseline)

This document defines the dependency/tooling baseline added for Phase 7 ticket P7-11.

The current app remains:

1. API: `apps/api` (stdlib server)
2. Frontend: `apps/frontend` (React + Vite)

The new framework scaffolds are additive only:

1. `apps/backend` (FastAPI scaffold)
2. `apps/frontend` (React + Vite scaffold)

## 1. Python Migration Tooling (FastAPI Baseline)

Dependencies are defined in `pyproject.toml` optional group `migration`.

Install (pip):

```bash
python3 -m pip install -e ".[migration]"
```

Run FastAPI scaffold:

```bash
uvicorn apps.backend.main:app --host 127.0.0.1 --port 8100 --reload
```

Run stdlib and FastAPI in parallel:

```bash
# terminal 1
python3 -m apps.api.server

# terminal 2
uvicorn apps.backend.main:app --host 127.0.0.1 --port 8100 --reload
```

Optional tooling commands:

```bash
ruff check apps/backend
mypy apps/backend
```

## 2. JS Migration Tooling (React + Vite Baseline)

Scaffold package manifest is in `apps/frontend/package.json`.

Install:

```bash
cd apps/frontend
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

## 3. Runtime Commands

Current API:

```bash
python3 -m apps.api.server
```

Frontend:

```bash
cd apps/frontend
npm run dev
```

Open:

```text
http://127.0.0.1:5174
```
