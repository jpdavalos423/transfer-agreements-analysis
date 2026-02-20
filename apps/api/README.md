# apps/api

Backend API service for pathway generation and metadata endpoints.

## Run locally

From repo root:

```bash
python3 -m apps.api.server
```

Optional environment variables:

1. `TPP_API_HOST` (default: `127.0.0.1`)
2. `TPP_API_PORT` (default: `8000`)
3. `TPP_API_CORS_ENABLED` (default: `true`)
4. `TPP_API_CORS_ALLOWED_ORIGINS` (default: `http://127.0.0.1:3000,http://localhost:3000,http://127.0.0.1:4173,http://localhost:4173,http://127.0.0.1:5173,http://localhost:5173`)
5. `TPP_API_LOG_LEVEL` (default: `SILENT`)

Endpoints:

```text
POST /v1/pathways/generate
GET /v1/metadata/colleges
GET /v1/metadata/districts
GET /v1/metadata/ucs
GET /v1/health
GET /v1/metrics
```

Reliability SLO check (valid-request success rate):

```bash
scripts/reliability_check --suite phase_a --repeat 2 --threshold 0.99
```

Product metrics endpoint:

```bash
curl -s http://127.0.0.1:8000/v1/metrics
```

See `docs/PRODUCT_METRICS.md` for metric definitions.
