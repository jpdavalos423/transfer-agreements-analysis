# apps/backend

FastAPI parallel API app for Phase 8 parity work. This does not replace `apps/api` yet.

## Run

```bash
uvicorn apps.backend.main:app --host 127.0.0.1 --port 8100 --reload
```

Or:

```bash
python3 -m apps.backend.main
```

Production-like profile:

```bash
scripts/run_backend_prod
```

## Route parity scaffold

Implemented `/v1` routes:

1. `POST /v1/pathways/generate`
2. `GET /v1/metadata/colleges`
3. `GET /v1/metadata/districts`
4. `GET /v1/metadata/ucs`
5. `GET /v1/metadata`
6. `GET /v1/health`
7. `GET /v1/metrics`

Routes call shared service-layer logic from `apps/api/services` and shared validators from `packages/shared_types`.
