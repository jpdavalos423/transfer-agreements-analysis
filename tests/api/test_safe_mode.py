import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

from apps.api.metadata_service import clear_metadata_cache
from apps.api.server import create_server
from packages.shared_types.v1 import validate_error_response_shape, validate_metadata_response_shape


class APISafeModeIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._original_runtime_dir = os.environ.get("TPP_RUNTIME_DIR")
        cls._tmp = tempfile.TemporaryDirectory()
        os.environ["TPP_RUNTIME_DIR"] = cls._tmp.name
        clear_metadata_cache()

        cls.server = create_server(host="127.0.0.1", port=0)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

        if cls._original_runtime_dir is None:
            os.environ.pop("TPP_RUNTIME_DIR", None)
        else:
            os.environ["TPP_RUNTIME_DIR"] = cls._original_runtime_dir
        clear_metadata_cache()
        cls._tmp.cleanup()

    def _get(self, path: str):
        return urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}", timeout=5)

    def _post_json(self, path: str, payload: dict):
        req = urllib.request.Request(
            url=f"http://127.0.0.1:{self.port}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        return urllib.request.urlopen(req, timeout=5)

    def test_metadata_endpoints_return_structured_payload_in_safe_mode(self):
        with self._get("/v1/metadata/colleges") as resp:
            self.assertEqual(resp.status, 200)
            payload = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(
            validate_metadata_response_shape(payload, kind="colleges"),
            [],
        )

        with self._get("/v1/metadata/districts") as resp:
            self.assertEqual(resp.status, 200)
            districts_payload = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(
            validate_metadata_response_shape(districts_payload, kind="districts"),
            [],
        )

        with self._get("/v1/metadata/ucs") as resp:
            self.assertEqual(resp.status, 200)
            ucs_payload = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(
            validate_metadata_response_shape(ucs_payload, kind="ucs"),
            [],
        )

    def test_generate_returns_structured_unavailable_error_in_safe_mode(self):
        payload = {
            "college_id": "de_anza",
            "target_ucs": ["UCLA"],
            "ge_pattern": "IGETC",
            "completed_courses": [],
        }
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._post_json("/v1/pathways/generate", payload)

        self.assertEqual(ctx.exception.code, 503)
        body = json.loads(ctx.exception.read().decode("utf-8"))
        self.assertEqual(validate_error_response_shape(body), [])
        self.assertEqual(body["error"]["code"], "PLANNER_UNAVAILABLE_DEGRADED")

    def test_health_reflects_degraded_status(self):
        with self._get("/v1/health") as resp:
            self.assertEqual(resp.status, 200)
            payload = json.loads(resp.read().decode("utf-8"))

        self.assertEqual(payload.get("status"), "degraded")
        self.assertEqual(payload.get("version"), "v1")
        runtime = payload.get("runtime", {})
        self.assertEqual(runtime.get("safe_mode"), True)
        self.assertIsInstance(runtime.get("reason"), str)


if __name__ == "__main__":
    unittest.main()
