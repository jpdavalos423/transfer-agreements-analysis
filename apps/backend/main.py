"""FastAPI app in parallel with stdlib API route parity for /v1."""

from __future__ import annotations

import json
import os
import uuid
from time import perf_counter
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from apps.api.config import APIServerConfig, load_api_server_config_from_env
from apps.api.metadata_service import load_runtime_metadata_with_safe_mode
from apps.api.metrics import APIMetrics
from apps.api.services import (
    GeneratePathwayInput,
    PathwayServiceError,
    build_health_response,
    build_metadata_aggregate_response,
    build_metadata_colleges_response,
    build_metadata_districts_response,
    build_metadata_ucs_response,
    generate_pathway,
)
from packages.shared_types.v1 import (
    ALLOWED_GE_PATTERNS,
    API_VERSION,
    build_error_response,
    validate_generate_request,
)


def create_app(config: APIServerConfig | None = None) -> FastAPI:
    app = FastAPI(title="Transfer Pathway API (FastAPI Parallel)")
    resolved = config or load_api_server_config_from_env()
    metrics = APIMetrics()

    def _request_id() -> str:
        return uuid.uuid4().hex

    def _origin_allowed(origin: str | None) -> bool:
        if not origin:
            return True
        return origin in set(resolved.cors_allowed_origins)

    def _apply_cors_headers(response: Response, origin: str | None) -> None:
        if not resolved.cors_enabled:
            return
        if origin and _origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"

    def _record(
        request: Request,
        *,
        status_code: int,
        payload: dict[str, Any],
        error_code: str | None = None,
        valid_request: bool | None = None,
        request_payload: Any = None,
        latency_ms: float | None = None,
    ) -> None:
        metrics.record(
            method=request.method,
            path=request.url.path,
            status_code=int(status_code),
            error_code=error_code,
            valid_request=valid_request,
            request_payload=request_payload,
            response_payload=payload,
            latency_ms=latency_ms,
        )

    def _error_response(
        request: Request,
        *,
        status_code: int,
        code: str,
        message: str,
        details: list[dict[str, str]] | None = None,
        request_id: str,
        valid_request: bool | None = None,
        request_payload: Any = None,
        latency_ms: float | None = None,
    ) -> JSONResponse:
        payload = build_error_response(
            code,
            message,
            details=details,
            status=status_code,
            request_id=request_id,
            path=request.url.path,
        )
        _record(
            request,
            status_code=status_code,
            payload=payload,
            error_code=code,
            valid_request=valid_request,
            request_payload=request_payload,
            latency_ms=latency_ms,
        )
        response = JSONResponse(status_code=status_code, content=payload)
        _apply_cors_headers(response, request.headers.get("Origin"))
        return response

    def _json_response(
        request: Request,
        *,
        status_code: int,
        payload: dict[str, Any],
        valid_request: bool | None = None,
        request_payload: Any = None,
        latency_ms: float | None = None,
    ) -> JSONResponse:
        _record(
            request,
            status_code=status_code,
            payload=payload,
            valid_request=valid_request,
            request_payload=request_payload,
            latency_ms=latency_ms,
        )
        response = JSONResponse(status_code=status_code, content=payload)
        _apply_cors_headers(response, request.headers.get("Origin"))
        return response

    def _not_found_response(request: Request, request_id: str) -> JSONResponse:
        return _error_response(
            request,
            status_code=404,
            code="NOT_FOUND",
            message="Route not found.",
            details=[
                {
                    "field": "path",
                    "message": (
                        "Use one of: POST /v1/pathways/generate, "
                        "GET /v1/metadata/colleges, GET /v1/metadata/districts, "
                        "GET /v1/metadata/ucs, GET /v1/health, GET /v1/metrics."
                    ),
                }
            ],
            request_id=request_id,
            valid_request=False,
        )

    @app.middleware("http")
    async def cors_guard(request: Request, call_next):
        origin = request.headers.get("Origin")
        if resolved.cors_enabled and origin and not _origin_allowed(origin):
            return _error_response(
                request,
                status_code=403,
                code="CORS_ORIGIN_FORBIDDEN",
                message="Origin is not allowed by CORS policy.",
                details=[{"field": "origin", "message": f"Origin not allowed: {origin}"}],
                request_id=_request_id(),
                valid_request=False,
            )
        if request.method.upper() == "OPTIONS":
            response = Response(status_code=204)
            _apply_cors_headers(response, origin)
            return response
        response = await call_next(request)
        _apply_cors_headers(response, origin)
        return response

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        if int(exc.status_code) == 404:
            return _not_found_response(request, _request_id())
        return _error_response(
            request,
            status_code=int(exc.status_code),
            code="HTTP_EXCEPTION",
            message=str(exc.detail) if exc.detail else "Request failed.",
            request_id=_request_id(),
            valid_request=False,
        )

    @app.exception_handler(HTTPException)
    async def fastapi_http_exception_handler(request: Request, exc: HTTPException):
        if int(exc.status_code) == 404:
            return _not_found_response(request, _request_id())
        return _error_response(
            request,
            status_code=int(exc.status_code),
            code="HTTP_EXCEPTION",
            message=str(exc.detail) if exc.detail else "Request failed.",
            request_id=_request_id(),
            valid_request=False,
        )

    @app.get("/v1/metrics")
    async def get_metrics(request: Request):
        return _json_response(
            request,
            status_code=200,
            payload=metrics.snapshot(),
            valid_request=True,
        )

    @app.get("/v1/metadata/colleges")
    async def get_metadata_colleges(request: Request):
        metadata, _, _ = load_runtime_metadata_with_safe_mode()
        return _json_response(
            request,
            status_code=200,
            payload=build_metadata_colleges_response(metadata),
            valid_request=True,
        )

    @app.get("/v1/metadata/districts")
    async def get_metadata_districts(request: Request):
        metadata, _, _ = load_runtime_metadata_with_safe_mode()
        return _json_response(
            request,
            status_code=200,
            payload=build_metadata_districts_response(metadata),
            valid_request=True,
        )

    @app.get("/v1/metadata/ucs")
    async def get_metadata_ucs(request: Request):
        metadata, _, _ = load_runtime_metadata_with_safe_mode()
        return _json_response(
            request,
            status_code=200,
            payload=build_metadata_ucs_response(metadata),
            valid_request=True,
        )

    @app.get("/v1/metadata")
    async def get_metadata_aggregate(request: Request):
        metadata, _, _ = load_runtime_metadata_with_safe_mode()
        return _json_response(
            request,
            status_code=200,
            payload=build_metadata_aggregate_response(
                metadata,
                allowed_ge_patterns=ALLOWED_GE_PATTERNS,
            ),
            valid_request=True,
        )

    @app.get("/v1/health")
    async def get_health(request: Request):
        metadata, is_degraded, degraded_reason = load_runtime_metadata_with_safe_mode()
        if is_degraded:
            payload = {
                "version": API_VERSION,
                "status": "degraded",
                "runtime": {
                    "dataset_version": metadata.manifest.get("version", ""),
                    "generated_at": metadata.manifest.get("generated_at", ""),
                    "row_counts": metadata.manifest.get("row_counts", {}),
                    "safe_mode": True,
                    "reason": degraded_reason or "",
                },
            }
            return _json_response(request, status_code=200, payload=payload, valid_request=True)

        return _json_response(
            request,
            status_code=200,
            payload=build_health_response(metadata),
            valid_request=True,
        )

    @app.post("/v1/pathways/generate")
    async def post_generate(request: Request):
        request_id = _request_id()
        metadata, is_degraded, degraded_reason = load_runtime_metadata_with_safe_mode()

        content_length = request.headers.get("Content-Length")
        if not content_length:
            return _error_response(
                request,
                status_code=400,
                code="INVALID_JSON",
                message="Missing Content-Length header.",
                request_id=request_id,
                valid_request=False,
            )

        payload: dict[str, Any] | None = None
        try:
            raw = await request.body()
            payload = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return _error_response(
                request,
                status_code=400,
                code="INVALID_JSON",
                message="Request body must be valid JSON.",
                request_id=request_id,
                valid_request=False,
                request_payload=payload,
            )

        if is_degraded:
            return _error_response(
                request,
                status_code=503,
                code="PLANNER_UNAVAILABLE_DEGRADED",
                message="Planner generation is unavailable while runtime artifacts are degraded.",
                details=[
                    {
                        "field": "runtime_metadata",
                        "message": degraded_reason or "Runtime artifacts are unavailable.",
                    }
                ],
                request_id=request_id,
                valid_request=False,
                request_payload=payload,
            )

        validation_errors = validate_generate_request(
            payload,
            allowed_colleges={item["id"] for item in metadata.colleges},
            allowed_ucs={item["id"] for item in metadata.ucs},
            allowed_ge_patterns=ALLOWED_GE_PATTERNS,
        )
        if validation_errors:
            return _error_response(
                request,
                status_code=400,
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=validation_errors,
                request_id=request_id,
                valid_request=False,
                request_payload=payload,
            )

        latency_ms: float | None = None
        try:
            start = perf_counter()
            response = generate_pathway(
                GeneratePathwayInput(
                    college_id=str(payload["college_id"]),
                    target_ucs=tuple(str(uc) for uc in payload["target_ucs"]),
                    ge_pattern=str(payload["ge_pattern"]),
                    completed_courses=tuple(str(course) for course in payload["completed_courses"]),
                    request_id=request_id,
                ),
                runtime_manifest=metadata.manifest,
            )
            latency_ms = (perf_counter() - start) * 1000.0
        except PathwayServiceError as exc:
            if latency_ms is None:
                latency_ms = (perf_counter() - start) * 1000.0
            return _error_response(
                request,
                status_code=exc.status,
                code=exc.code,
                message=exc.message,
                details=exc.details,
                request_id=request_id,
                valid_request=True,
                request_payload=payload,
                latency_ms=latency_ms,
            )

        return _json_response(
            request,
            status_code=200,
            payload=response,
            valid_request=True,
            request_payload=payload,
            latency_ms=latency_ms,
        )

    return app


app = create_app()


def run(host: str | None = None, port: int | None = None) -> None:
    import uvicorn

    bind_host = host or os.environ.get("TPP_FASTAPI_HOST", "127.0.0.1")
    bind_port = int(port or os.environ.get("TPP_FASTAPI_PORT", "8100"))
    uvicorn.run("apps.backend.main:app", host=bind_host, port=bind_port, reload=False)


if __name__ == "__main__":
    run()
