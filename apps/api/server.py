"""Minimal API server for vertical-slice endpoint P0-1."""

from __future__ import annotations

import json
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from packages.shared_types.v1 import (
    ALLOWED_GE_PATTERNS,
    API_VERSION,
    build_error_response,
    normalize_warning_payloads,
    validate_generate_request,
)
from apps.api.planner_service import PlannerServiceError, generate_pathway_response
from apps.api.metadata_service import load_runtime_metadata


class PathwayRequestHandler(BaseHTTPRequestHandler):
    server_version = "TransferPathwayAPI/0.1"

    def _set_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, status_code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802 (stdlib naming)
        self.send_response(HTTPStatus.NO_CONTENT)
        self._set_cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _request_id(self) -> str:
        return uuid.uuid4().hex

    def _runtime_metadata(self):
        try:
            return load_runtime_metadata(), None
        except Exception as exc:  # pragma: no cover - defensive server fallback
            return None, exc

    def _send_error(
        self,
        status: int,
        *,
        code: str,
        message: str,
        request_id: str,
        path: str,
        details: list[dict[str, str]] | None = None,
    ) -> None:
        self._send_json(
            status,
            build_error_response(
                code,
                message,
                details=details,
                status=status,
                request_id=request_id,
                path=path,
            ),
        )

    def _normalize_path(self) -> str:
        return self.path.split("?", 1)[0]

    def do_POST(self) -> None:  # noqa: N802 (stdlib naming)
        path = self._normalize_path()
        request_id = self._request_id()
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
            )
            return

        metadata, metadata_err = self._runtime_metadata()
        if metadata_err is not None:
            self._send_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                code="RUNTIME_METADATA_ERROR",
                message="Unable to load metadata from runtime artifacts.",
                request_id=request_id,
                path=path,
                details=[{"field": "runtime_metadata", "message": str(metadata_err)}],
            )
            return

        content_length = self.headers.get("Content-Length")
        if not content_length:
            self._send_error(
                HTTPStatus.BAD_REQUEST,
                code="INVALID_JSON",
                message="Missing Content-Length header.",
                request_id=request_id,
                path=path,
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
            )
            return

        try:
            response = generate_pathway_response(payload)
        except PlannerServiceError as exc:
            self._send_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                code="PLANNER_RUNTIME_ERROR",
                message="Unable to generate pathway response from runtime artifacts.",
                request_id=request_id,
                path=path,
                details=[{"field": "planner_service", "message": str(exc)}],
            )
            return

        response.setdefault("meta", {})
        response["request_id"] = request_id
        response["warnings"] = normalize_warning_payloads(
            response.get("warnings"),
            trace_id=request_id,
            default_source="planner_core",
            default_severity="WARN",
        )
        response["meta"]["runtime"] = {
            "dataset_version": metadata.manifest.get("version"),
            "generated_at": metadata.manifest.get("generated_at"),
        }
        self._send_json(HTTPStatus.OK, response)

    def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
        path = self._normalize_path()
        request_id = self._request_id()
        metadata, metadata_err = self._runtime_metadata()
        if metadata_err is not None:
            status = (
                HTTPStatus.SERVICE_UNAVAILABLE
                if path == "/v1/health"
                else HTTPStatus.INTERNAL_SERVER_ERROR
            )
            self._send_error(
                status,
                code="RUNTIME_METADATA_ERROR",
                message="Unable to load metadata from runtime artifacts.",
                request_id=request_id,
                path=path,
                details=[{"field": "runtime_metadata", "message": str(metadata_err)}],
            )
            return

        if path == "/v1/metadata/colleges":
            self._send_json(
                HTTPStatus.OK,
                {
                    "version": API_VERSION,
                    "data": metadata.colleges,
                },
            )
            return
        if path == "/v1/metadata/districts":
            self._send_json(
                HTTPStatus.OK,
                {
                    "version": API_VERSION,
                    "data": metadata.districts,
                },
            )
            return
        if path == "/v1/metadata/ucs":
            self._send_json(
                HTTPStatus.OK,
                {
                    "version": API_VERSION,
                    "data": metadata.ucs,
                },
            )
            return
        if path == "/v1/metadata":
            # Backward-compatible aggregate metadata endpoint.
            self._send_json(
                HTTPStatus.OK,
                {
                    "version": API_VERSION,
                    "colleges": metadata.colleges,
                    "districts": metadata.districts,
                    "ucs": metadata.ucs,
                    "ge_patterns": sorted(ALLOWED_GE_PATTERNS),
                },
            )
            return
        if path == "/v1/health":
            self._send_json(
                HTTPStatus.OK,
                {
                    "version": API_VERSION,
                    "status": "ok",
                    "runtime": {
                        "dataset_version": metadata.manifest.get("version", ""),
                        "generated_at": metadata.manifest.get("generated_at", ""),
                        "row_counts": metadata.manifest.get("row_counts", {}),
                    },
                },
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
                        "GET /v1/metadata/ucs, GET /v1/health."
                    ),
                }
            ],
        )

    def log_message(self, fmt: str, *args: Any) -> None:
        # Keep output concise in tests and local runs.
        return


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), PathwayRequestHandler)


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = create_server(host=host, port=port)
    print(f"API listening on http://{host}:{server.server_address[1]}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
