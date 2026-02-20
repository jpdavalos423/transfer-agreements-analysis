# apps/frontend

React + Vite frontend for Transfer Pathway Planner.

## Run Commands

Start API (terminal 1):

```bash
python3 -m apps.api.server
```

Run React + Vite app (terminal 2):

```bash
cd apps/frontend
npm install
npm run dev
```

Open Vite app:

- `http://127.0.0.1:5174` (or the port printed by Vite)

## Configuration

API base URL resolution order:

1. `window.__TPP_CONFIG__.apiBaseUrl` from `public/config.js`
2. `window.__TPP_API_BASE_URL`
3. `VITE_API_BASE_URL`
4. default `http://127.0.0.1:8000`

Example using Vite env var:

```bash
cd apps/frontend
VITE_API_BASE_URL=http://127.0.0.1:9000 npm run dev
```

## Verification

```bash
cd apps/frontend
npm run typecheck
npm run a11y:check
npm run test:client
npm run test:ui
```

Shared contract types are imported from:

- `packages/shared_types/v1/types.ts`

## Flow Implemented

- Setup workflow (`/`): college + UC targets + GE pattern + completed courses
- Pathway page (`/pathway`): loading/success/error/idle states
- Warnings panel + confidence label
- Deterministic rendering order matching API output (no client-side sorting)
