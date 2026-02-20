import json
import threading
import unittest
import urllib.error
import urllib.request

from apps.api.config import APIServerConfig
from apps.api.server import create_server


class APICorsIntegrationTest(unittest.TestCase):
    def _start_server(self, config: APIServerConfig):
        server = create_server(host="127.0.0.1", port=0, config=config)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread

    def _stop_server(self, server, thread):
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    def _options(self, port: int, path: str, origin: str):
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}{path}",
            method="OPTIONS",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
            },
        )
        return urllib.request.urlopen(req, timeout=5)

    def test_default_localhost_origin_is_allowed(self):
        server, thread = self._start_server(APIServerConfig())
        try:
            with self._options(server.server_address[1], "/v1/pathways/generate", "http://localhost:5173") as resp:
                self.assertEqual(resp.status, 204)
                self.assertEqual(
                    resp.headers.get("Access-Control-Allow-Origin"),
                    "http://localhost:5173",
                )
        finally:
            self._stop_server(server, thread)

    def test_disallowed_origin_is_rejected_with_allowlist(self):
        server, thread = self._start_server(
            APIServerConfig(
                cors_enabled=True,
                cors_allowed_origins=("https://app.example.com",),
            )
        )
        try:
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                self._options(server.server_address[1], "/v1/pathways/generate", "https://evil.example.com")

            self.assertEqual(ctx.exception.code, 403)
            body = json.loads(ctx.exception.read().decode("utf-8"))
            self.assertEqual(body["error"]["code"], "CORS_ORIGIN_FORBIDDEN")
        finally:
            self._stop_server(server, thread)


if __name__ == "__main__":
    unittest.main()
