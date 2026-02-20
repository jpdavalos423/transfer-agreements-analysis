from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request
from typing import Any

from apps.api.server import create_server as create_stdlib_server
from packages.shared_types.v1 import validate_metrics_response_shape
from tests.api_fastapi.parity_harness import semantic_parity_compare


class MetricsObservabilityParityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from fastapi.testclient import TestClient
        except Exception as exc:  # pragma: no cover
            raise unittest.SkipTest(f"FastAPI test client unavailable: {exc}")

        from apps.backend.main import create_app

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
        cls.stdlib_server.shutdown()
        cls.stdlib_server.server_close()
        cls.stdlib_thread.join(timeout=2)

    def _stdlib_request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        return_raw: bool = False,
    ) -> tuple[int, dict[str, Any], str]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url=f"http://127.0.0.1:{self.stdlib_port}{path}",
            data=data,
            headers={"Content-Type": "application/json"} if payload is not None else {},
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                raw = resp.read().decode("utf-8")
                payload_obj = json.loads(raw)
                return resp.status, payload_obj, raw if return_raw else ""
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            payload_obj = json.loads(raw)
            return exc.code, payload_obj, raw if return_raw else ""

    def _fastapi_request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        return_raw: bool = False,
    ) -> tuple[int, dict[str, Any], str]:
        response = self.fastapi_client.request(method, path, json=payload)
        raw = response.text
        return response.status_code, response.json(), raw if return_raw else ""

    def _apply_identical_traffic(self) -> None:
        calls: list[tuple[str, str, dict[str, Any] | None]] = [
            ("GET", "/v1/health", None),
            ("GET", "/v1/metadata/ucs", None),
            (
                "POST",
                "/v1/pathways/generate",
                {
                    "college_id": "de_anza",
                    "target_ucs": ["UCLA", "UCSD"],
                    "ge_pattern": "IGETC",
                    "completed_courses": ["MATH 1A"],
                },
            ),
            (
                "POST",
                "/v1/pathways/generate",
                {
                    "college_id": "de_anza",
                    "target_ucs": ["UCLA"],
                    "ge_pattern": "IGETC",
                    "completed_courses": [],
                },
            ),
        ]

        for method, path, payload in calls:
            std_status, _, _ = self._stdlib_request(method, path, payload)
            fast_status, _, _ = self._fastapi_request(method, path, payload)
            self.assertEqual(std_status, fast_status, f"Status mismatch for {method} {path}")

    def _key_order_signature(self, value: Any) -> Any:
        if isinstance(value, dict):
            keys = list(value.keys())
            return {"__keys__": keys, "items": {k: self._key_order_signature(value[k]) for k in keys}}
        if isinstance(value, list):
            return [self._key_order_signature(item) for item in value]
        return type(value).__name__

    def test_metrics_parity_after_identical_traffic(self):
        self._apply_identical_traffic()

        std_status, std_payload, _ = self._stdlib_request("GET", "/v1/metrics")
        fast_status, fast_payload, _ = self._fastapi_request("GET", "/v1/metrics")

        self.assertEqual(std_status, 200)
        self.assertEqual(fast_status, 200)
        self.assertEqual(validate_metrics_response_shape(std_payload), [])
        self.assertEqual(validate_metrics_response_shape(fast_payload), [])

        ok, diff = semantic_parity_compare(std_payload, fast_payload)
        self.assertTrue(ok, msg=diff)

    def test_metrics_stable_across_repeated_calls(self):
        self._apply_identical_traffic()

        std_status_1, std_payload_1, std_raw_1 = self._stdlib_request(
            "GET", "/v1/metrics", return_raw=True
        )
        std_status_2, std_payload_2, std_raw_2 = self._stdlib_request(
            "GET", "/v1/metrics", return_raw=True
        )
        fast_status_1, fast_payload_1, fast_raw_1 = self._fastapi_request(
            "GET", "/v1/metrics", return_raw=True
        )
        fast_status_2, fast_payload_2, fast_raw_2 = self._fastapi_request(
            "GET", "/v1/metrics", return_raw=True
        )

        self.assertEqual(std_status_1, 200)
        self.assertEqual(std_status_2, 200)
        self.assertEqual(fast_status_1, 200)
        self.assertEqual(fast_status_2, 200)

        self.assertEqual(std_payload_1, std_payload_2)
        self.assertEqual(fast_payload_1, fast_payload_2)

        # Serialized output should remain stable for repeated calls on each stack.
        self.assertEqual(std_raw_1, std_raw_2)
        self.assertEqual(fast_raw_1, fast_raw_2)

        # Key ordering signature should be stable and parity-aligned.
        self.assertEqual(
            self._key_order_signature(std_payload_1),
            self._key_order_signature(std_payload_2),
        )
        self.assertEqual(
            self._key_order_signature(fast_payload_1),
            self._key_order_signature(fast_payload_2),
        )

        ok, diff = semantic_parity_compare(std_payload_1, fast_payload_1)
        self.assertTrue(ok, msg=diff)


if __name__ == "__main__":
    unittest.main()
