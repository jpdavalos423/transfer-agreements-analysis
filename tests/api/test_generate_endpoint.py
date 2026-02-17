import json
import threading
import unittest
import urllib.error
import urllib.request

from apps.api.server import create_server
from packages.shared_types.v1 import validate_generate_response_shape


class GenerateEndpointIntegrationTest(unittest.TestCase):
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

    def test_generate_returns_200_and_v1_shape(self):
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

    def test_generate_returns_structured_validation_error(self):
        invalid_payload = {
            "college_id": "de_anza",
            "target_ucs": ["UCB"],  # out of subset
            "ge_pattern": "IGETC",
            "completed_courses": [],
        }
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._post_json("/v1/pathways/generate", invalid_payload)

        self.assertEqual(ctx.exception.code, 400)
        body = json.loads(ctx.exception.read().decode("utf-8"))
        self.assertEqual(body.get("version"), "v1")
        self.assertIn("error", body)
        self.assertEqual(body["error"].get("code"), "VALIDATION_ERROR")
        self.assertIsInstance(body["error"].get("details"), list)


if __name__ == "__main__":
    unittest.main()

