import json
import threading
import unittest
import urllib.error
import urllib.request
from typing import Any

from apps.api.server import create_server as create_stdlib_server
from packages.shared_types.v1 import (
    validate_error_response_shape,
    validate_generate_response_shape,
    validate_health_response_shape,
    validate_metadata_response_shape,
    validate_metrics_response_shape,
)


class FastAPIContractParityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from fastapi.testclient import TestClient
        except Exception as exc:  # pragma: no cover
            raise unittest.SkipTest(f"FastAPI test client unavailable: {exc}")

        from apps.backend.main import create_app

        cls._TestClient = TestClient
        cls.fastapi_client = TestClient(create_app())

        cls.stdlib_server = create_stdlib_server(host="127.0.0.1", port=0)
        cls.stdlib_port = cls.stdlib_server.server_address[1]
        cls.stdlib_thread = threading.Thread(
            target=cls.stdlib_server.serve_forever,
            daemon=True,
        )
        cls.stdlib_thread.start()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "stdlib_server"):
            cls.stdlib_server.shutdown()
            cls.stdlib_server.server_close()
            cls.stdlib_thread.join(timeout=2)

    def _stdlib_request(self, method: str, path: str, payload: dict[str, Any] | None = None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url=f"http://127.0.0.1:{self.stdlib_port}{path}",
            data=data,
            headers={"Content-Type": "application/json"} if payload is not None else {},
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def _fastapi_request(self, method: str, path: str, payload: dict[str, Any] | None = None):
        resp = self.fastapi_client.request(method, path, json=payload)
        return resp.status_code, resp.json()

    def _normalize_for_parity(self, payload: Any) -> Any:
        if isinstance(payload, dict):
            normalized = {}
            for key, value in payload.items():
                if key == "request_id":
                    continue
                if key == "trace_id":
                    continue
                normalized[key] = self._normalize_for_parity(value)
            return normalized
        if isinstance(payload, list):
            return [self._normalize_for_parity(item) for item in payload]
        return payload

    def _type_shape(self, payload: Any) -> Any:
        if isinstance(payload, dict):
            return {key: self._type_shape(payload[key]) for key in sorted(payload)}
        if isinstance(payload, list):
            if not payload:
                return []
            return [self._type_shape(payload[0])]
        return type(payload).__name__

    def test_generate_success_parity(self):
        request_payload = {
            "college_id": "de_anza",
            "target_ucs": ["UCLA", "UCSD"],
            "ge_pattern": "IGETC",
            "completed_courses": ["MATH 1A"],
        }

        std_status, std_payload = self._stdlib_request("POST", "/v1/pathways/generate", request_payload)
        fast_status, fast_payload = self._fastapi_request("POST", "/v1/pathways/generate", request_payload)

        self.assertEqual(std_status, 200)
        self.assertEqual(fast_status, 200)
        self.assertEqual(validate_generate_response_shape(std_payload), [])
        self.assertEqual(validate_generate_response_shape(fast_payload), [])
        self.assertEqual(
            self._normalize_for_parity(std_payload),
            self._normalize_for_parity(fast_payload),
        )

    def test_generate_validation_error_parity(self):
        request_payload = {
            "college_id": "__bad__",
            "target_ucs": ["UCLA"],
            "ge_pattern": "IGETC",
            "completed_courses": [],
        }

        std_status, std_payload = self._stdlib_request("POST", "/v1/pathways/generate", request_payload)
        fast_status, fast_payload = self._fastapi_request("POST", "/v1/pathways/generate", request_payload)

        self.assertEqual(std_status, 400)
        self.assertEqual(fast_status, 400)
        self.assertEqual(validate_error_response_shape(std_payload), [])
        self.assertEqual(validate_error_response_shape(fast_payload), [])
        self.assertEqual(
            self._normalize_for_parity(std_payload),
            self._normalize_for_parity(fast_payload),
        )

    def test_not_found_error_parity(self):
        std_status, std_payload = self._stdlib_request("GET", "/v1/not-a-real-route")
        fast_status, fast_payload = self._fastapi_request("GET", "/v1/not-a-real-route")

        self.assertEqual(std_status, 404)
        self.assertEqual(fast_status, 404)
        self.assertEqual(validate_error_response_shape(std_payload), [])
        self.assertEqual(validate_error_response_shape(fast_payload), [])
        self.assertEqual(
            self._normalize_for_parity(std_payload),
            self._normalize_for_parity(fast_payload),
        )

    def test_metadata_health_metrics_shape_parity(self):
        for path, validator, kind in [
            ("/v1/metadata/colleges", validate_metadata_response_shape, "colleges"),
            ("/v1/metadata/districts", validate_metadata_response_shape, "districts"),
            ("/v1/metadata/ucs", validate_metadata_response_shape, "ucs"),
        ]:
            std_status, std_payload = self._stdlib_request("GET", path)
            fast_status, fast_payload = self._fastapi_request("GET", path)
            self.assertEqual(std_status, 200)
            self.assertEqual(fast_status, 200)
            self.assertEqual(validator(std_payload, kind=kind), [])
            self.assertEqual(validator(fast_payload, kind=kind), [])
            self.assertEqual(std_payload, fast_payload)

        std_status, std_payload = self._stdlib_request("GET", "/v1/health")
        fast_status, fast_payload = self._fastapi_request("GET", "/v1/health")
        self.assertEqual(std_status, 200)
        self.assertEqual(fast_status, 200)
        self.assertEqual(validate_health_response_shape(std_payload), [])
        self.assertEqual(validate_health_response_shape(fast_payload), [])
        self.assertEqual(std_payload, fast_payload)

        # Exercise generate once on both so metrics contains route entries.
        request_payload = {
            "college_id": "de_anza",
            "target_ucs": ["UCLA"],
            "ge_pattern": "IGETC",
            "completed_courses": [],
        }
        self._stdlib_request("POST", "/v1/pathways/generate", request_payload)
        self._fastapi_request("POST", "/v1/pathways/generate", request_payload)

        std_status, std_payload = self._stdlib_request("GET", "/v1/metrics")
        fast_status, fast_payload = self._fastapi_request("GET", "/v1/metrics")
        self.assertEqual(std_status, 200)
        self.assertEqual(fast_status, 200)
        self.assertEqual(validate_metrics_response_shape(std_payload), [])
        self.assertEqual(validate_metrics_response_shape(fast_payload), [])
        self.assertEqual(self._type_shape(std_payload), self._type_shape(fast_payload))


if __name__ == "__main__":
    unittest.main()
