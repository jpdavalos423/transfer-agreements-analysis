# apps/api

Backend API service for pathway generation and metadata endpoints.

## Run locally

From repo root:

```bash
python3 -m apps.api.server
```

Default endpoint:

```text
POST /v1/pathways/generate
```

Subset metadata endpoint:

```text
GET /v1/metadata
```
