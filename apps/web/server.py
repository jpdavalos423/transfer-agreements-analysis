"""Minimal static file server for the web MVP."""

from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def create_server(host: str = "127.0.0.1", port: int = 5173) -> ThreadingHTTPServer:
    web_root = Path(__file__).resolve().parent
    handler = partial(SimpleHTTPRequestHandler, directory=str(web_root))
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

