"""Minimal API server for vertical-slice endpoint P0-1."""

from __future__ import annotations

import json
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from time import perf_counter
from typing import Any

from apps.api.config import APIServerConfig, load_api_server_config_from_env
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
from apps.api.metadata_service import load_runtime_metadata_with_safe_mode


class PathwayRequestHandler(BaseHTTPRequestHandler):
    server_version = "TransferPathwayAPI/0.1"

    def _cors_enabled(self) -> bool:
        return bool(getattr(self.server, "api_cors_enabled", True))

    def _cors_allowed_origins(self) -> set[str]:
        configured = getattr(self.server, "api_cors_allowed_origins", ())
        if isinstance(configured, (tuple, list, set)):
            return {str(item) for item in configured}
        return set()

    def _is_origin_allowed(self, origin: str | None) -> bool:
        if not origin:
            return True
        return origin in self._cors_allowed_origins()

    def _set_cors_headers(self, *, origin: str | None = None) -> None:
        if not bool(getattr(self.server, "api_cors_enabled", True)):
            return
        if origin and self._is_origin_allowed(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _metrics(self) -> APIMetrics:
        metrics = getattr(self.server, "api_metrics", None)
        if isinstance(metrics, APIMetrics):
            return metrics
        fallback = APIMetrics()
        setattr(self.server, "api_metrics", fallback)
        return fallback

    def _send_json(
        self,
        status_code: int,
        payload: dict[str, Any],
        *,
        path: str,
        error_code: str | None = None,
        valid_request: bool | None = None,
        request_payload: Any = None,
        latency_ms: float | None = None,
    ) -> None:
        body = json.dumps(payload).encode("utf-8")
        self._metrics().record(
            method=self.command,
            path=path,
            status_code=int(status_code),
            error_code=error_code,
            valid_request=valid_request,
            request_payload=request_payload,
            response_payload=payload,
            latency_ms=latency_ms,
        )
        self.send_response(status_code)
        self._set_cors_headers(origin=self.headers.get("Origin"))
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802 (stdlib naming)
        origin = self.headers.get("Origin")
        path = self._normalize_path()
        request_id = self._request_id()
        if self._cors_enabled() and origin and not self._is_origin_allowed(origin):
            self._send_error(
                HTTPStatus.FORBIDDEN,
                code="CORS_ORIGIN_FORBIDDEN",
                message="Origin is not allowed by CORS policy.",
                request_id=request_id,
                path=path,
                details=[{"field": "origin", "message": f"Origin not allowed: {origin}"}],
                valid_request=False,
            )
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self._set_cors_headers(origin=origin)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _request_id(self) -> str:
        return uuid.uuid4().hex

    def _runtime_metadata(self):
        return load_runtime_metadata_with_safe_mode()

    def _send_error(
        self,
        status: int,
        *,
        code: str,
        message: str,
        request_id: str,
        path: str,
        details: list[dict[str, str]] | None = None,
        valid_request: bool | None = None,
        request_payload: Any = None,
        latency_ms: float | None = None,
    ) -> None:
        payload = build_error_response(
            code,
            message,
            details=details,
            status=status,
            request_id=request_id,
            path=path,
        )
        self._send_json(
            status,
            payload,
            path=path,
            error_code=code,
            valid_request=valid_request,
            request_payload=request_payload,
            latency_ms=latency_ms,
        )

    def _normalize_path(self) -> str:
        return self.path.split("?", 1)[0]

    def do_POST(self) -> None:  # noqa: N802 (stdlib naming)
        path = self._normalize_path()
        request_id = self._request_id()
        origin = self.headers.get("Origin")
        if self._cors_enabled() and origin and not self._is_origin_allowed(origin):
            self._send_error(
                HTTPStatus.FORBIDDEN,
                code="CORS_ORIGIN_FORBIDDEN",
                message="Origin is not allowed by CORS policy.",
                request_id=request_id,
                path=path,
                details=[{"field": "origin", "message": f"Origin not allowed: {origin}"}],
                valid_request=False,
            )
            return
        if path != "/v1/pathways/generate":
            self._send_error(
                HTTPStatus.NOT_FOUND,
                code="NOT_FOUND",
                message="Route not found.",
                request_id=request_id,
                path=path,
                details=[
                    {
                        "field": "path",
                        "message": "Use POST /v1/pathways/generate.",
                    }
                ],
                valid_request=False,
            )
            return

        payload: dict[str, Any] | None = None
        metadata, is_degraded, degraded_reason = self._runtime_metadata()

        content_length = self.headers.get("Content-Length")
        if not content_length:
            self._send_error(
                HTTPStatus.BAD_REQUEST,
                code="INVALID_JSON",
                message="Missing Content-Length header.",
                request_id=request_id,
                path=path,
                valid_request=False,
                request_payload=payload,
            )
            return

        try:
            raw = self.rfile.read(int(content_length))
            payload = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self._send_error(
                HTTPStatus.BAD_REQUEST,
                code="INVALID_JSON",
                message="Request body must be valid JSON.",
                request_id=request_id,
                path=path,
                valid_request=False,
                request_payload=payload,
            )
            return

        if is_degraded:
            self._send_error(
                HTTPStatus.SERVICE_UNAVAILABLE,
                code="PLANNER_UNAVAILABLE_DEGRADED",
                message="Planner generation is unavailable while runtime artifacts are degraded.",
                request_id=request_id,
                path=path,
                details=[
                    {
                        "field": "runtime_metadata",
                        "message": degraded_reason or "Runtime artifacts are unavailable.",
                    }
                ],
                valid_request=False,
                request_payload=payload,
            )
            return

        validation_errors = validate_generate_request(
            payload,
            allowed_colleges={item["id"] for item in metadata.colleges},
            allowed_ucs={item["id"] for item in metadata.ucs},
            allowed_ge_patterns=ALLOWED_GE_PATTERNS,
        )
        if validation_errors:
            self._send_error(
                HTTPStatus.BAD_REQUEST,
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                request_id=request_id,
                path=path,
                details=validation_errors,
                valid_request=False,
                request_payload=payload,
            )
            return

        latency_ms: float | None = None
        try:
            start = perf_counter()
            response = generate_pathway(
                GeneratePathwayInput(
                    college_id=str(payload["college_id"]),
                    target_ucs=tuple(str(uc) for uc in payload["target_ucs"]),
                    ge_pattern=str(payload["ge_pattern"]),
                    completed_courses=tuple(
                        str(course) for course in payload["completed_courses"]
                    ),
                    request_id=request_id,
                ),
                runtime_manifest=metadata.manifest,
            )
            latency_ms = (perf_counter() - start) * 1000.0
        except PathwayServiceError as exc:
            if latency_ms is None:
                latency_ms = (perf_counter() - start) * 1000.0
            self._send_error(
                exc.status,
                code=exc.code,
                message=exc.message,
                request_id=request_id,
                path=path,
                details=exc.details,
                valid_request=True,
                request_payload=payload,
                latency_ms=latency_ms,
            )
            return

        self._send_json(
            HTTPStatus.OK,
            response,
            path=path,
            valid_request=True,
            request_payload=payload,
            latency_ms=latency_ms,
        )

    def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
        path = self._normalize_path()
        request_id = self._request_id()
        origin = self.headers.get("Origin")
        if self._cors_enabled() and origin and not self._is_origin_allowed(origin):
            self._send_error(
                HTTPStatus.FORBIDDEN,
                code="CORS_ORIGIN_FORBIDDEN",
                message="Origin is not allowed by CORS policy.",
                request_id=request_id,
                path=path,
                details=[{"field": "origin", "message": f"Origin not allowed: {origin}"}],
                valid_request=False,
            )
            return
        if path == "/v1/metrics":
            self._send_json(
                HTTPStatus.OK,
                self._metrics().snapshot(),
                path=path,
                valid_request=True,
            )
            return
        metadata, is_degraded, degraded_reason = self._runtime_metadata()

        if path == "/v1/metadata/colleges":
            self._send_json(
                HTTPStatus.OK,
                build_metadata_colleges_response(metadata),
                path=path,
                valid_request=True,
            )
            return
        if path == "/v1/metadata/districts":
            self._send_json(
                HTTPStatus.OK,
                build_metadata_districts_response(metadata),
                path=path,
                valid_request=True,
            )
            return
        if path == "/v1/metadata/ucs":
            self._send_json(
                HTTPStatus.OK,
                build_metadata_ucs_response(metadata),
                path=path,
                valid_request=True,
            )
            return
        if path == "/v1/metadata":
            # Backward-compatible aggregate metadata endpoint.
            self._send_json(
                HTTPStatus.OK,
                build_metadata_aggregate_response(
                    metadata,
                    allowed_ge_patterns=ALLOWED_GE_PATTERNS,
                ),
                path=path,
                valid_request=True,
            )
            return
        if path == "/v1/health":
            if is_degraded:
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "version": API_VERSION,
                        "status": "degraded",
                        "runtime": {
                            "dataset_version": metadata.manifest.get("version", ""),
                            "generated_at": metadata.manifest.get("generated_at", ""),
                            "row_counts": metadata.manifest.get("row_counts", {}),
                            "safe_mode": True,
                            "reason": degraded_reason or "",
                        },
                    },
                    path=path,
                    valid_request=True,
                )
            else:
                self._send_json(
                    HTTPStatus.OK,
                    build_health_response(metadata),
                    path=path,
                    valid_request=True,
                )
            return

        self._send_error(
            HTTPStatus.NOT_FOUND,
            code="NOT_FOUND",
            message="Route not found.",
            request_id=request_id,
            path=path,
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
            valid_request=False,
        )

    def log_message(self, fmt: str, *args: Any) -> None:
        level = str(getattr(self.server, "api_log_level", "SILENT")).upper()
        if level == "SILENT":
            return
        super().log_message(fmt, *args)


def create_server(
    host: str | None = None,
    port: int | None = None,
    *,
    config: APIServerConfig | None = None,
) -> ThreadingHTTPServer:
    resolved = config or load_api_server_config_from_env()
    bind_host = host if host is not None else resolved.host
    bind_port = port if port is not None else resolved.port
    server = ThreadingHTTPServer((bind_host, bind_port), PathwayRequestHandler)
    setattr(server, "api_metrics", APIMetrics())
    setattr(server, "api_cors_enabled", resolved.cors_enabled)
    setattr(server, "api_cors_allowed_origins", resolved.cors_allowed_origins)
    setattr(server, "api_log_level", resolved.log_level)
    return server


def run(host: str | None = None, port: int | None = None) -> None:
    server = create_server(host=host, port=port)
    bound_host, bound_port = server.server_address
    print(f"API listening on http://{bound_host}:{bound_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
