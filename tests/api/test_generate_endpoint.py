import json
import threading
import unittest
import urllib.error
import urllib.request

from apps.api.server import create_server
from packages.shared_types.v1 import (
    validate_error_response_shape,
    validate_generate_response_shape,
    validate_health_response_shape,
    validate_metadata_response_shape,
)


class APIIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server(host="127.0.0.1", port=0)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def _post_json(self, path: str, payload: dict):
        url = f"http://127.0.0.1:{self.port}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url=url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        return urllib.request.urlopen(req, timeout=5)

    def _get(self, path: str):
        url = f"http://127.0.0.1:{self.port}{path}"
        return urllib.request.urlopen(url, timeout=5)

    def test_generate_success_response_shape(self):
        payload = {
            "college_id": "de_anza",
            "target_ucs": ["UCLA", "UCSD"],
            "ge_pattern": "IGETC",
            "completed_courses": ["MATH 1A"],
        }
        with self._post_json("/v1/pathways/generate", payload) as resp:
            self.assertEqual(resp.status, 200)
            body = json.loads(resp.read().decode("utf-8"))

        shape_errors = validate_generate_response_shape(body)
        self.assertEqual(shape_errors, [], f"Response shape errors: {shape_errors}")
        request_id = body.get("request_id")
        self.assertIsInstance(request_id, str)
        self.assertTrue(request_id)
        for warning in body.get("warnings", []):
            self.assertEqual(warning.get("trace_id"), request_id)

    def test_generate_reject_unknown_college(self):
        invalid_payload = {
            "college_id": "__unknown_college__",
            "target_ucs": ["UCLA"],
            "ge_pattern": "IGETC",
            "completed_courses": [],
        }
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._post_json("/v1/pathways/generate", invalid_payload)

        self.assertEqual(ctx.exception.code, 400)
        body = json.loads(ctx.exception.read().decode("utf-8"))
        shape_errors = validate_error_response_shape(body)
        self.assertEqual(shape_errors, [], f"Error shape errors: {shape_errors}")
        self.assertEqual(body["error"].get("code"), "VALIDATION_ERROR")
        fields = {d.get("field") for d in body["error"]["details"] if isinstance(d, dict)}
        self.assertIn("college_id", fields)

    def test_generate_reject_unknown_uc(self):
        invalid_payload = {
            "college_id": "de_anza",
            "target_ucs": ["UCZZ"],
            "ge_pattern": "IGETC",
            "completed_courses": [],
        }
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._post_json("/v1/pathways/generate", invalid_payload)

        self.assertEqual(ctx.exception.code, 400)
        body = json.loads(ctx.exception.read().decode("utf-8"))
        shape_errors = validate_error_response_shape(body)
        self.assertEqual(shape_errors, [], f"Error shape errors: {shape_errors}")
        self.assertEqual(body["error"].get("code"), "VALIDATION_ERROR")
        fields = {d.get("field") for d in body["error"]["details"] if isinstance(d, dict)}
        self.assertIn("target_ucs[0]", fields)

    def test_metadata_colleges_endpoint(self):
        with self._get("/v1/metadata/colleges") as resp:
            self.assertEqual(resp.status, 200)
            body = json.loads(resp.read().decode("utf-8"))
        shape_errors = validate_metadata_response_shape(body, kind="colleges")
        self.assertEqual(shape_errors, [], f"Colleges shape errors: {shape_errors}")
        ids = [item["id"] for item in body["data"]]
        self.assertEqual(ids, sorted(ids))

    def test_metadata_districts_endpoint(self):
        with self._get("/v1/metadata/districts") as resp:
            self.assertEqual(resp.status, 200)
            body = json.loads(resp.read().decode("utf-8"))
        shape_errors = validate_metadata_response_shape(body, kind="districts")
        self.assertEqual(shape_errors, [], f"Districts shape errors: {shape_errors}")
        ids = [item["id"] for item in body["data"]]
        self.assertEqual(ids, sorted(ids))

    def test_metadata_ucs_endpoint(self):
        with self._get("/v1/metadata/ucs") as resp:
            self.assertEqual(resp.status, 200)
            body = json.loads(resp.read().decode("utf-8"))
        shape_errors = validate_metadata_response_shape(body, kind="ucs")
        self.assertEqual(shape_errors, [], f"UCs shape errors: {shape_errors}")
        ids = [item["id"] for item in body["data"]]
        self.assertEqual(ids, sorted(ids))

    def test_health_endpoint(self):
        with self._get("/v1/health") as resp:
            self.assertEqual(resp.status, 200)
            body = json.loads(resp.read().decode("utf-8"))
        shape_errors = validate_health_response_shape(body)
        self.assertEqual(shape_errors, [], f"Health shape errors: {shape_errors}")

    def test_unknown_route_returns_standard_error_envelope(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._get("/v1/not-a-real-route")
        self.assertEqual(ctx.exception.code, 404)
        body = json.loads(ctx.exception.read().decode("utf-8"))
        shape_errors = validate_error_response_shape(body)
        self.assertEqual(shape_errors, [], f"Error shape errors: {shape_errors}")
        self.assertEqual(body["error"]["code"], "NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
