"""Minimal static file server for the web MVP."""

from __future__ import annotations

import json
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from pathlib import Path

_DEFAULT_WEB_API_BASE_URL = "http://127.0.0.1:8000"


class PlannerWebRequestHandler(SimpleHTTPRequestHandler):
    def _write_dynamic_config(self) -> None:
        payload = {
            "apiBaseUrl": os.environ.get(
                "TPP_WEB_API_BASE_URL",
                _DEFAULT_WEB_API_BASE_URL,
            )
        }
        body = (
            f"window.__TPP_CONFIG__ = {json.dumps(payload, sort_keys=True)};\n"
            "window.__TPP_API_BASE_URL = window.__TPP_CONFIG__.apiBaseUrl;\n"
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/javascript; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.path = "/index.html"
        elif parsed.path == "/pathway":
            self.path = "/pathway.html"
        elif parsed.path == "/config.js":
            self._write_dynamic_config()
            return
        super().do_GET()


def create_server(host: str = "127.0.0.1", port: int = 5173) -> ThreadingHTTPServer:
    web_root = Path(__file__).resolve().parent
    handler = partial(PlannerWebRequestHandler, directory=str(web_root))
    return ThreadingHTTPServer((host, port), handler)


def run(host: str = "127.0.0.1", port: int = 5173) -> None:
    server = create_server(host=host, port=port)
    print(f"Web UI listening on http://{host}:{server.server_address[1]}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
