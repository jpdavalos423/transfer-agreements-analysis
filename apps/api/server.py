"""Minimal API server for vertical-slice endpoint P0-1."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from packages.shared_types.v1 import (
    API_VERSION,
    build_error_response,
    validate_generate_request,
)


class PathwayRequestHandler(BaseHTTPRequestHandler):
    server_version = "TransferPathwayAPI/0.1"

    def _set_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
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

    def do_POST(self) -> None:  # noqa: N802 (stdlib naming)
        if self.path != "/v1/pathways/generate":
            self._send_json(
                HTTPStatus.NOT_FOUND,
                build_error_response(
                    "NOT_FOUND",
                    "Route not found.",
                    [{"field": "path", "message": "Use POST /v1/pathways/generate."}],
                ),
            )
            return

        content_length = self.headers.get("Content-Length")
        if not content_length:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                build_error_response(
                    "INVALID_JSON",
                    "Missing Content-Length header.",
                ),
            )
            return

        try:
            raw = self.rfile.read(int(content_length))
            payload = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                build_error_response("INVALID_JSON", "Request body must be valid JSON."),
            )
            return

        validation_errors = validate_generate_request(payload)
        if validation_errors:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                build_error_response(
                    "VALIDATION_ERROR",
                    "Request validation failed.",
                    validation_errors,
                ),
            )
            return

        # Stubbed vertical-slice response; planner implementation is deferred.
        response = {
            "version": API_VERSION,
            "plan": [],
            "warnings": [
                {
                    "code": "PLANNER_NOT_IMPLEMENTED",
                    "message": "Planner logic is not implemented yet; returning stub response.",
                }
            ],
            "meta": {
                "college_id": payload["college_id"],
                "target_ucs": payload["target_ucs"],
                "ge_pattern": payload["ge_pattern"],
                "completed_courses_count": len(payload["completed_courses"]),
            },
        }
        self._send_json(HTTPStatus.OK, response)

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
