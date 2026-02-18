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
    validate_metrics_response_shape,
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

    def _get_metrics(self) -> dict:
        with self._get("/v1/metrics") as resp:
            self.assertEqual(resp.status, 200)
            metrics = json.loads(resp.read().decode("utf-8"))
        shape_errors = validate_metrics_response_shape(metrics)
        self.assertEqual(shape_errors, [], f"Metrics shape errors: {shape_errors}")
        return metrics

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

    def test_generate_known_prereq_college_avoids_prereq_gap_warning(self):
        payload = {
            "college_id": "cabrillo",
            "target_ucs": ["UCLA"],
            "ge_pattern": "IGETC",
            "completed_courses": [],
        }
        with self._post_json("/v1/pathways/generate", payload) as resp:
            self.assertEqual(resp.status, 200)
            body = json.loads(resp.read().decode("utf-8"))

        warning_codes = [
            warning.get("code")
            for warning in body.get("warnings", [])
            if isinstance(warning, dict)
        ]
        self.assertNotIn("PREREQ_GAP", warning_codes)

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

    def test_metrics_endpoint_and_reliability_counters(self):
        valid_payload = {
            "college_id": "de_anza",
            "target_ucs": ["UCLA", "UCSD"],
            "ge_pattern": "IGETC",
            "completed_courses": ["MATH 1A"],
        }
        invalid_payload = {
            "college_id": "__unknown_college__",
            "target_ucs": ["UCLA"],
            "ge_pattern": "IGETC",
            "completed_courses": [],
        }

        with self._post_json("/v1/pathways/generate", valid_payload) as resp:
            self.assertEqual(resp.status, 200)

        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._post_json("/v1/pathways/generate", invalid_payload)
        self.assertEqual(ctx.exception.code, 400)

        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._get("/v1/not-a-real-route")
        self.assertEqual(ctx.exception.code, 404)

        metrics = self._get_metrics()

        totals = metrics["totals"]
        self.assertGreaterEqual(totals["request_count"], 3)
        self.assertGreaterEqual(totals["success_count"], 1)
        self.assertGreaterEqual(totals["error_count"], 2)
        self.assertGreaterEqual(totals["error_count_by_code"].get("VALIDATION_ERROR", 0), 1)
        self.assertGreaterEqual(totals["error_count_by_code"].get("NOT_FOUND", 0), 1)

        route_metrics = None
        for route in metrics["by_route"]:
            if route.get("method") == "POST" and route.get("path") == "/v1/pathways/generate":
                route_metrics = route
                break
        self.assertIsNotNone(route_metrics)
        self.assertGreaterEqual(route_metrics["valid_request_count"], 1)
        self.assertGreaterEqual(route_metrics["valid_success_count"], 1)
        self.assertGreaterEqual(route_metrics["valid_success_rate"], 0.99)

        product = metrics["product"]
        self.assertGreaterEqual(product["pathway_generation_requests_total"], 2)
        self.assertGreaterEqual(product["pathway_generation_valid_requests_total"], 1)
        self.assertGreaterEqual(product["pathway_generation_success_total"], 1)
        self.assertIsInstance(product["top_target_uc_sets"], list)
        self.assertIsInstance(product["ge_pattern_usage"], list)
        self.assertIsInstance(product["latency_histogram_ms"], list)
        buckets = [item["bucket"] for item in product["latency_histogram_ms"]]
        self.assertEqual(
            buckets,
            [
                "le_50ms",
                "le_100ms",
                "le_250ms",
                "le_500ms",
                "le_1000ms",
                "le_2000ms",
                "gt_2000ms",
            ],
        )
        for item in product["top_target_uc_sets"]:
            targets = item.get("uc_targets", [])
            self.assertEqual(targets, sorted(set(targets)))

    def test_metrics_product_counters_increment_after_valid_generation(self):
        before = self._get_metrics()["product"]

        payload = {
            "college_id": "de_anza",
            "target_ucs": ["UCLA", "UCSD"],
            "ge_pattern": "IGETC",
            "completed_courses": [],
        }
        with self._post_json("/v1/pathways/generate", payload) as resp:
            self.assertEqual(resp.status, 200)

        after = self._get_metrics()["product"]
        self.assertEqual(
            after["pathway_generation_requests_total"],
            before["pathway_generation_requests_total"] + 1,
        )
        self.assertEqual(
            after["pathway_generation_valid_requests_total"],
            before["pathway_generation_valid_requests_total"] + 1,
        )
        self.assertEqual(
            after["pathway_generation_success_total"],
            before["pathway_generation_success_total"] + 1,
        )

        def _target_count(product_block: dict, uc_targets: tuple[str, ...]) -> int:
            for item in product_block.get("top_target_uc_sets", []):
                if tuple(item.get("uc_targets", [])) == uc_targets:
                    return int(item.get("count", 0))
            return 0

        self.assertEqual(
            _target_count(after, ("UCLA", "UCSD")),
            _target_count(before, ("UCLA", "UCSD")) + 1,
        )

        def _ge_count(product_block: dict, ge_pattern: str) -> int:
            for item in product_block.get("ge_pattern_usage", []):
                if item.get("ge_pattern") == ge_pattern:
                    return int(item.get("count", 0))
            return 0

        self.assertEqual(
            _ge_count(after, "IGETC"),
            _ge_count(before, "IGETC") + 1,
        )

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
