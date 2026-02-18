# apps/api

Backend API service for pathway generation and metadata endpoints.

## Run locally

From repo root:

```bash
python3 -m apps.api.server
```

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
